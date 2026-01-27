import { BarChart3, BookOpenText, Users } from "lucide-react";

function ProgressCard({ completion, courses, student }) {
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
          <p className="progress-title">Total Completion Rate</p>
        </div>

        {/* Card 2 */}
        <div className="progress-card">
          <div className="progress-card-flex">
            <BookOpenText className="progress-icon" />
            <h3 className="progress-value">{courses}</h3>
          </div>
          <p className="progress-title">Total Course</p>
        </div>

        {/* Card 3 */}
        <div className="progress-card">
          <div className="progress-card-flex">
            <Users className="progress-icon" />
            <h3 className="progress-value">{student}</h3>
          </div>
          <p className="progress-title">Total Student</p>
        </div>
      </div>
    </div>
  );
}

export default ProgressCard;

