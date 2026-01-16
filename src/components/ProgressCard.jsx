import { BarChart3, Trophy, Clock } from "lucide-react";

function ProgressCard({ completion, courses, time }) {
  return (
    <div className="progress-section">
      {/* <h2>Your Progress</h2> */}
      <div className="progress-cards">
        {/* Card 1 */}
        <div className="progress-card">
          <div className="progress-card-flex">
            <BarChart3 className="progress-icon" />
            <h3 className="progress-value">{completion}%</h3>
          </div>
          <p className="progress-title">Overall Completion</p>
        </div>

        {/* Card 2 */}
        <div className="progress-card">
          <div className="progress-card-flex">
            <Trophy className="progress-icon" />
            <h3 className="progress-value">{courses}</h3>
          </div>
          <p className="progress-title">Courses Completed</p>
        </div>

        {/* Card 3 */}
        <div className="progress-card">
          <div className="progress-card-flex">
            <Clock className="progress-icon" />
            <h3 className="progress-value">{time}h</h3>
          </div>
          <p className="progress-title">Learning Time</p>
        </div>
      </div>
    </div>
  );
}

export default ProgressCard;

