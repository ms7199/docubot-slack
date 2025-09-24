from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os, json
from rag import create_chat_chain
from pinecone_client import init_pinecone
from embeddings import load_embeddings
from pdf_processor import process_pdf_files, chunk_documents, store_documents
from utils import _safe_get_score_and_metadata
from typing import List, Dict, Any

# initialize externally in main, but we create helper wrappers here to be used by main
def create_slack_app(index, embeddings):
    app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
    chat_chain = create_chat_chain()

    def _say_index_stats(say, stats):
        """Format index stats nicely."""
        try:
            stats_dict = dict(stats) if not isinstance(stats, dict) else stats
            pretty = json.dumps(stats_dict, indent=2)
        except Exception:
            pretty = str(stats)
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": "*📊 Pinecone Index Stats*"}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"```{pretty}```"}} 
        ]
        say(blocks=blocks, text="Index stats")

    def _say_no_docs(say):
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": "*No relevant documents found.* :mag: \nTry adding PDFs to `./pdfs` and run `/reload_pdfs`."}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Tip: PDFs with selectable text work best (not scanned images)."}]}
        ]
        say(blocks=blocks, text="No documents found")

    def _say_reload_progress(say, uploaded_count):
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"🔄 *PDF knowledge base reloaded.*\nUploaded *{uploaded_count}* document chunks to Pinecone."}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Use `/index_stats` to inspect the index."}]}
        ]
        say(blocks=blocks, text="Reload complete")

    def _say_llm_response(say, llm_text: str, sources: List[str], context_preview: str = None):
        blocks = []
        # LLM answer
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*🤖 Answer*\n{llm_text}"}})
        blocks.append({"type": "divider"})

        # Context preview
        if context_preview and context_preview.strip() and context_preview != "No relevant documents found.":
            # Trim context preview to avoid flooding Slack
            preview = context_preview
            if len(preview) > 800:
                preview = preview[:800] + "...\n\n*(context truncated)*"
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Context used:*\n```{preview}```"}})
            blocks.append({"type": "divider"})

        # Sources
        if sources:
            source_text = ", ".join(sorted(sources))
            blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"📚 *Sources consulted:* {source_text}"}]})
        else:
            blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "📚 *Sources consulted:* None"}]})

        # Small footer
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "You can re-ingest docs with `/reload_pdfs`."}]})

        say(blocks=blocks, text="LLM response")

    @app.message(".*")
    def message_handler(message, say, logger):
        try:
            user_msg = message.get("text", "")
            print("Incoming Slack message:", user_msg)

            if not user_msg or not user_msg.strip():
                say("Please send a non-empty message.")
                return

            # Commands
            if user_msg.lower().startswith("/reload_pdfs"):
                say(blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "🔄 *Reloading PDF knowledge base...*"}}], text="Reloading")
                documents = process_pdf_files("./pdfs")
                if not documents:
                    _say_no_docs(say)
                    return
                chunked = chunk_documents(documents)
                store_documents(index, embeddings, chunked)
                # Count uploaded vectors roughly from chunked length
                uploaded_count = len(chunked)
                _say_reload_progress(say, uploaded_count)
                return

            if user_msg.lower().startswith("/index_stats"):
                if index:
                    try:
                        stats = index.describe_index_stats()
                        _say_index_stats(say, stats)
                    except Exception as e:
                        say(blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"❌ Error getting index stats: `{e}`"}}], text="Index error")
                else:
                    say(blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "❌ Pinecone index not available."}}], text="Index not available")
                return

            # Normal query flow
            if not embeddings or not index:
                say(blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "⚠️ RAG unavailable: embeddings or index not configured. Use `/reload_pdfs` after fixing setup."}}], text="RAG unavailable")
                return

            # create query embedding and search
            query_embedding = embeddings.embed_query(user_msg)
            search_res = index.query(vector=query_embedding, top_k=5, include_metadata=True)
            matches = search_res.matches if hasattr(search_res, "matches") else (search_res.get("matches") if isinstance(search_res, dict) else search_res)

            # prepare context
            if not matches:
                context = "No relevant documents found."
            else:
                parts = []
                for i, r in enumerate(matches):
                    score, meta = _safe_get_score_and_metadata(r)
                    preview = meta.get("content_preview", "")
                    parts.append(f"Doc {i+1} — {meta.get('source','Unknown')} (score {score:.3f})\n{preview}")
                context = "\n\n".join(parts)

            # call LLM
            combined_input = f"Context from documents:\n{context}\n\nHuman Question: {user_msg}"
            try:
                response = chat_chain.predict(input=combined_input).strip()
            except Exception as e:
                print("Error from LLM:", e)
                response = "I'm sorry, I encountered an error processing your request."

            # gather sources
            sources = set()
            if matches:
                for r in matches:
                    _, meta = _safe_get_score_and_metadata(r)
                    sources.add(meta.get("source", "Unknown"))

            # send prettified response
            _say_llm_response(say, response, list(sources), context if matches else None)

        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            say(blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"❌ Sorry, I encountered an error: `{str(e)}`"}}], text="Handler error")

    @app.event("file_shared")
    def handle_file_upload(event, say, logger):
        try:
            file_info = event.get("file", {})
            if file_info.get("mimetype") == "application/pdf":
                say(blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "📎 PDF detected. Save it to `./pdfs` and run `/reload_pdfs` to ingest it."}}], text="PDF detected")
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")

    return app
