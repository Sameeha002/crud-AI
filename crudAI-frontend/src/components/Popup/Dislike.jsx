import { useState } from "react";
import "./Dislike.css";
import FeedbackService from "../Services/FeedbackService";


const Dislike = ({ threadId, messageId, modalId }) => {
  const [input, setInput] = useState("");

  const handleSubmit = () => {
    console.log(input);
    if (threadId && messageId) {
      FeedbackService(threadId, messageId, "dislike", input); // save to DB
    }
    setInput("");
  };
  return (
    <div
      className="modal fade"
      id={modalId}
      tabIndex="-1"
      aria-labelledby="exampleModalLabel"
      aria-hidden="true"
    >
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content bg-dark text-light">
          <div className="modal-header border-secondary">
            <h1 className="modal-title fs-5" id="exampleModalLabel">
              Feedback
            </h1>
            <button
              type="button"
              className="btn-close btn-close-white"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div className="modal-body">
            <label>Please provide details:</label>
            <input
              type="message"
              placeholder="What was unsatisfying about this response?"
              className="feedback-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
          </div>
          <div className="modal-footer border-secondary">
            <button
              type="button"
              className="btn btn-secondary"
              data-bs-dismiss="modal"
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleSubmit}
              data-bs-dismiss = "modal"
            >
              Submit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dislike;
