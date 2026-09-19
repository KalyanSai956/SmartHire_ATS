export default function QuestionPanel({ question, questionNumber }) {
  if (!question) {
    return null;
  }

  return <section className="arena-question-card"></section>;
}
