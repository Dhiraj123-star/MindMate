# --- Import Libraries ---
import streamlit as st
import requests
import time
import io  # For creating downloadable report files

# --- ThinkTool Class Definition ---
class ThinkTool:
    def __init__(self, api_key, model="claude-3-opus-20240229", show_thinking=True, max_tokens=1000):
        """Initialize ThinkTool with API key, model, and token length."""
        self.api_key = api_key
        self.model = model
        self.show_thinking = show_thinking
        self.api_url = self._get_api_url()  # Dynamically set the correct API URL
        self.max_tokens = max_tokens  # Dynamically adjustable max_tokens

    def _get_api_url(self):
        """Return the correct API URL for Claude."""
        if "claude" in self.model.lower():
            return "https://api.anthropic.com/v1/messages"  # Claude API endpoint
        else:
            raise ValueError(f"Unknown model: {self.model}")

    def think(self, problem):
        """Generate structured thinking steps using the Claude model."""
        try:
            prompt = f"""
            I need to solve this problem: {problem}
            
            Please help me think through this step-by-step.
            Only provide individual steps, each starting with "Step: ".
            Don't provide a final answer yet.
            """
            response = self._call_api(prompt)

            thinking_text = response.get('content', [{}])[0].get('text', '')
            thinking_steps = [
                step.replace("Step: ", "").strip()
                for step in thinking_text.split('\n')
                if step.strip().startswith("Step:")
            ]

            if not thinking_steps:
                thinking_steps = [
                    line.strip()
                    for line in thinking_text.split('\n')
                    if line.strip()
                ]

            return thinking_steps

        except Exception as e:
            return [f"Error during thinking: {str(e)}"]

    def answer(self, problem, thinking=None):
        """Generate final answer based on thinking steps."""
        try:
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

            response = self._call_api(prompt)
            answer_text = response.get('content', [{}])[0].get('text', 'No answer generated')
            return answer_text

        except Exception as e:
            return f"Error during answering: {str(e)}"

    def _call_api(self, prompt):
        """Call the Claude API with retries."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }

        max_retries = 3  # Retry 3 times max
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(self.api_url, headers=headers, json=data, timeout=15)

                if response.status_code == 401:
                    raise Exception("Unauthorized: Invalid API Key.")
                elif response.status_code == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                elif response.status_code >= 500:
                    raise Exception(f"Server error ({response.status_code}). Try again later.")
                elif response.status_code != 200:
                    raise Exception(f"Request failed: {response.status_code} {response.text}")

                return response.json()

            except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                if attempt == max_retries:
                    raise Exception(f"Request failed after {max_retries} attempts. Error: {str(e)}")
                else:
                    time.sleep(1)  # Wait 1 second before retrying

# --- Streamlit App UI ---

# Title of the app: catchy production-grade name
st.title("🧠 MindMate - Your Thoughtful Assistant")

# --- Sidebar: Settings ---
st.sidebar.header("Settings")

# Input: API Key (hidden)
api_key = st.sidebar.text_input("API Key", type="password")

# Select Claude Model
model = st.sidebar.selectbox("Select Claude Model", [
    "claude-3-5-sonnet-20241022",  
    "claude-3-7-sonnet-20250219", 
])

# Select Thinking Detail Level
thinking_detail = st.sidebar.radio(
    "Choose the level of thinking detail:",
    ("Short", "Medium", "Detailed"),
    index=1  # Default is Medium
)

# Set max_tokens based on user's choice
tokens_dict = {
    "Short": 500,
    "Medium": 1000,
    "Detailed": 2000
}
max_tokens = tokens_dict[thinking_detail]

# --- Main Area ---

# Problem text input
problem = st.text_area("Describe your problem here...", height=200)

# Solve Button
if st.button("Solve"):
    if not api_key or not problem:
        st.error("Please enter your API key and a problem!")
    else:
        tool = ThinkTool(api_key, model, max_tokens=max_tokens)

        with st.spinner("Thinking..."):
            try:
                # Generate thinking steps
                thinking = tool.think(problem)

                # Generate final answer
                final_answer = tool.answer(problem, thinking)

                # Typing-style animation for thinking steps
                st.subheader("🧠 Thinking Steps:")
                placeholder = st.empty()
                full_text = ""

                for step in thinking:
                    full_text += f"- {step}\n"
                    placeholder.markdown(full_text)
                    time.sleep(0.5)

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
                st.error(f"Oops! {e}")

# --- Sidebar: Show previous problems (optional) ---
if "history" in st.session_state and st.session_state.history:
    st.sidebar.subheader("Previous Problems")
    for idx, item in enumerate(st.session_state.history[::-1], 1):
        st.sidebar.markdown(f"**{idx}.** {item['problem']}")
