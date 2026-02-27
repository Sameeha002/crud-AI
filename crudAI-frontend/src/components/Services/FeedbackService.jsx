import axios from "axios";
import { toast } from "react-toastify";

const FeedbackService = async (
  thread_id,
  message_id,
  feedbackType,
  reason = null,
) => {
  try {
    const res = await axios.post(
      `http://127.0.0.1:8000/users/chats/${thread_id}/messages/${message_id}/feedback`,
      {
        feedback_type: feedbackType,
        reason: reason,
      }
    );
    toast.success("Response submitted!");
    return res.data
  } catch (error) {
    console.log("failed to save feedback", error)
    toast.error("Failed to submit feedback.");
  }
};

export default FeedbackService;
