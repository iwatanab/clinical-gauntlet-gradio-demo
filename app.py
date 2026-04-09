import gradio as gr
from models import Argument
from pipeline import run_pipeline


def submit(claim: str, grounds: str, warrant: str, backing: str) -> dict:
    argument = Argument(
        claim=claim,
        grounds=grounds,
        warrant=warrant if warrant.strip() else None,
        backing=backing if backing.strip() else None,
    )
    return run_pipeline(argument)


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            claim = gr.Textbox(label="Claim", lines=3)
            grounds = gr.Textbox(label="Grounds", lines=3)
            warrant = gr.Textbox(label="Warrant", lines=2)
            backing = gr.Textbox(label="Backing", lines=2)
            submit_btn = gr.Button("Submit")
        with gr.Column():
            output = gr.JSON(label="Output")

    submit_btn.click(
        fn=submit,
        inputs=[claim, grounds, warrant, backing],
        outputs=output,
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
