# --- Import Libraries ---
import streamlit as st
import requests
import time
import io  # For creating downloadable report files

# --- ThinkTool Class Definition ---
class ThinkTool:
    def __init__(self, api_key, model="claude-3-opus-20240229", show_thinking=True):
        """Initialize ThinkTool with API key and model."""
        self.api_key = api_key
        self.model = model
        self.show_thinking = show_thinking
        self.api_url = "https://api.anthropic.com/v1/messages"

    def think(self, problem):
        """Generate structured thinking steps using Claude API."""
        prompt = f"""
        I need to solve this problem: {problem}
        
        Please help me think through this step-by-step.
        Only provide individual steps, each starting with "Step: ".
        Don't provide a final answer yet.
        """
        response = self._call_claude_api(prompt)
        
        thinking_text = response.get('content', [{}])[0].get('text', '')
        thinking_steps = [
            step.replace("Step: ", "").strip()
            for step in thinking_text.split('\n')
            if step.strip().startswith("Step:")
        ]

        # Fallback if no "Step:" found
        if not thinking_steps:
            thinking_steps = [
                line.strip()
                for line in thinking_text.split('\n')
                if line.strip()
            ]

        return thinking_steps

    def answer(self, problem, thinking=None):
        """Generate final answer based on thinking steps."""
        if thinking:
            thinking_text = "\n".join([f"- {step}" for step in thinking])
            prompt = f"""
            Problem: {problem}

            Thinking steps:
            {thinking_text}

            Now, based on the above, provide a clear final answer without repeating all steps.
            """
        else:
            prompt = f"""
            Problem: {problem}

            What is the final answer? Provide a clear and concise solution.
            """
        
        response = self._call_claude_api(prompt)
        answer_text = response.get('content', [{}])[0].get('text', 'No answer generated')
        return answer_text

    def _call_claude_api(self, prompt):
        """Call Anthropic Claude API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": self.model,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(self.api_url, headers=headers, json=data)

        if response.status_code != 200:
            raise Exception(f"API request failed [{response.status_code}]: {response.text}")

        return response.json()

# --- Streamlit App UI ---

# Title of the app: catchy production-grade name
st.title("🧠 MindMate - Your Thoughtful Assistant")

# --- Sidebar: Settings ---
st.sidebar.header("Settings")

# Input: API Key (hidden)
api_key = st.sidebar.text_input("API Key", type="password")

# Select Model
model = st.sidebar.selectbox("Model", [
    "claude-3-5-sonnet-20241022",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-haiku-20241022"
])

# --- Main Area ---

# Problem text input
problem = st.text_area("Describe your problem here...", height=200)

# Solve Button
if st.button("Solve"):
    if not api_key or not problem:
        st.error("Please enter your API key and a problem!")
    else:
        tool = ThinkTool(api_key, model)

        with st.spinner("Thinking...") as spinner:  # Enhanced spinner with dots animation
            try:
                # Generate thinking steps
                thinking = tool.think(problem)

                # Generate final answer
                final_answer = tool.answer(problem, thinking)

                # Typing-style animation for thinking steps
                st.subheader("🧠 Thinking Steps:")
                placeholder = st.empty()  # Placeholder for live update
                full_text = ""  # Initialize empty text

                # Display thinking step-by-step with animation
                for step in thinking:
                    full_text += f"- {step}\n"
                    placeholder.markdown(full_text)
                    time.sleep(0.5)  # Small delay for animation effect

                # Display final answer
                st.subheader("✅ Final Answer:")
                st.success(final_answer)

                # Save to session history
                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.append({
                    "problem": problem,
                    "thinking": thinking,
                    "answer": final_answer
                })

                # Build report text
                report = f"Problem:\n{problem}\n\nThinking Steps:\n"
                report += "\n".join(f"- {step}" for step in thinking)
                report += f"\n\nFinal Answer:\n{final_answer}"

                # Create in-memory file for download
                buffer = io.BytesIO()
                buffer.write(report.encode())
                buffer.seek(0)

                # Download Button
                st.download_button(
                    label="📥 Download Thinking Report",
                    data=buffer,
                    file_name="thinking_report.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"Error: {e}")

# --- Sidebar: Show previous problems (optional) ---
if "history" in st.session_state and st.session_state.history:
    st.sidebar.subheader("Previous Problems")
    for idx, item in enumerate(st.session_state.history[::-1], 1):
        st.sidebar.markdown(f"**{idx}.** {item['problem']}")
