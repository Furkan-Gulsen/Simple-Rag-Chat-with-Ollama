import streamlit as st
from pathlib import Path
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.backend.core.services.chat_manager import ChatManager

ALLOWED_FILE_TYPES = ["txt", "pdf", "py", "js", "java", "cpp", "h", "c", "cs"]

class StreamlitUI:
    def __init__(self):
        self.chat_manager = ChatManager()
        self._initialize_session_state()
        
    def _initialize_session_state(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "current_session_id" not in st.session_state:
            st.session_state.current_session_id = None
        if "show_file_uploader" not in st.session_state:
            st.session_state.show_file_uploader = True
            
    def render_header(self):
        st.title("Simple RAG Chat 🤖")
        
    def render_sidebar(self):
        if st.sidebar.button("➕ New Session", type="primary"):
            self._reset_session()
            
        st.sidebar.title("Chat Sessions")
        self._render_session_list()
        st.sidebar.divider()
        self._render_current_session_info()
        
    def _reset_session(self):
        st.session_state.show_file_uploader = True
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.rerun()
        
    def _render_session_list(self):
        sessions = self.chat_manager.get_all_sessions()
        if not sessions:
            st.sidebar.info("No previous sessions found")
            return
            
        for session in sessions:
            session_time = session["last_accessed"].strftime("%Y-%m-%d %H:%M")
            session_title = f"{session['filename']} ({session_time})"
            
            if st.sidebar.button(
                session_title,
                key=f"session_{session['session_id']}",
                help=f"Messages: {session['message_count']}"
            ):
                self._load_session(session["session_id"])
                
    def _load_session(self, session_id: str):
        if self.chat_manager.load_session(session_id):
            st.session_state.current_session_id = session_id
            st.session_state.messages = self.chat_manager.get_chat_history_for_session(session_id)
            st.session_state.show_file_uploader = False
            st.rerun()
        
    def _render_current_session_info(self):
        current_session_id = st.session_state.current_session_id
        if current_session_id:
            session = self.chat_manager.get_session(current_session_id)
            if session:
                st.sidebar.markdown("### Current Session")
                st.sidebar.markdown(f"**File:** {session['filename']}")
                st.sidebar.markdown(f"**Created:** {session['created_at'].strftime('%Y-%m-%d %H:%M')}")
                st.sidebar.markdown(f"**Messages:** {session['message_count']}")
                
    def render_file_uploader(self):
        if st.session_state.show_file_uploader:
            uploaded_file = st.file_uploader(
                "Upload a file to start chatting",
                type=ALLOWED_FILE_TYPES,
                key="file_uploader"
            )
            
            if uploaded_file:
                current_session_id = st.session_state.current_session_id
                last_file_name = st.session_state.get("last_file_name")
                
                if not current_session_id or uploaded_file.name != last_file_name:
                    self._process_uploaded_file(uploaded_file)
                    
    def _process_uploaded_file(self, uploaded_file):
        with st.spinner("Processing file..."):
            try:
                if len(uploaded_file.getvalue()) > 10 * 1024 * 1024:
                    st.error("File size exceeds 10MB limit")
                    return
                    
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
            
                session_id = self.chat_manager.create_session(uploaded_file.name, tmp_path)
                if not session_id:
                    raise ValueError("Failed to create session")
                    
                st.session_state.current_session_id = session_id
                st.session_state.show_file_uploader = False
                st.session_state.messages = []
                st.session_state.last_file_name = uploaded_file.name
                st.success(f"File processed: {uploaded_file.name}")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.session_state.show_file_uploader = True
            
    def render_chat_interface(self):
        current_session_id = st.session_state.current_session_id
        show_file_uploader = st.session_state.show_file_uploader
        
        if not current_session_id:
            if not show_file_uploader:
                st.info("Please click '➕ New Session' to start a new chat or select an existing session.")
            return
            
        self._render_chat_messages()
        self._handle_chat_input()
        
    def _render_chat_messages(self):
        chat_container = st.container()
        with chat_container:
            messages = st.session_state.messages
            
            if not messages:
                st.info("No messages yet. Start the conversation!")
                return
                
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    st.caption(f"_{message.get('timestamp', datetime.utcnow()).strftime('%H:%M:%S')}_")
                    
    def _handle_chat_input(self):
        if prompt := st.chat_input("Ask a question about the code"):
            self._add_user_message(prompt)
            self._get_ai_response(prompt)
            
    def _add_user_message(self, content: str):
        message = {
            "role": "user",
            "content": content,
            "timestamp": datetime.utcnow()
        }
        st.session_state.messages.append(message)
        with st.chat_message("user"):
            st.markdown(content)
            st.caption(f"_{message['timestamp'].strftime('%H:%M:%S')}_")
            
    def _get_ai_response(self, prompt: str):
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    current_session_id = st.session_state.current_session_id
                    response = self.chat_manager.query(current_session_id, prompt)
                    st.markdown(response)
                    self._add_assistant_message(response)
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    st.error(error_message)
                    self._add_assistant_message(error_message)
                    
    def _add_assistant_message(self, content: str):
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": datetime.utcnow()
        }
        st.session_state.messages.append(message)
        st.caption(f"_{message['timestamp'].strftime('%H:%M:%S')}_")
        
    def run(self):
        self.render_header()
        self.render_sidebar()
        self.render_file_uploader()
        self.render_chat_interface()

if __name__ == "__main__":
    ui = StreamlitUI()
    ui.run()
