import { useState } from "react";
import { Brain, Cloud, Bot, Search, Filter, Code } from "lucide-react";
import Sidebar from "../components/SideBar";
import Header from "../components/Header";
import { courses } from "../data/courses";
import CourseCard from "../components/CourseCard";
import ProgressCard from "../components/ProgressCard";




function StudentDashboard() {
  // search and Filter
  const [search, setSearch] = useState("");

  // 🔹 progress state
  const [completion] = useState(65);
  const [coursesCompleted] = useState(12);

  const [learningTime] = useState(48);

  // chatBot 
  const [isChatOpen, setIsChatOpen] = useState(false);

  // this is used for filtering the course (Array Filtering)
  const filteredCourses = courses.filter((course) =>
    course.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="dashboard-layout">
      <Sidebar onChatClick={() => setIsChatOpen(true)} />

      <div className="main-content">
        <Header />

        {/* 🔹 Progress Section goes HERE */}
        <ProgressCard
          completion={completion}
          courses={coursesCompleted}
          time={learningTime}
        />

        {/* 🔹 Courses Header Row */}
        <div className="courses-header">
          <h2>Your Courses</h2>

          <div className="course-actions">
            <div className="search-box">
              <Search size={16} />
              <input
                type="text"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <button className="filter-btn">
              <Filter size={16} />
              Filter
            </button>
          </div>
        </div>

        {/* 📦 Course Grid */}
        <div className="course-grid">
          {filteredCourses.map((course) => (
            <CourseCard key={course.id} {...course} />
          ))}

        </div>
      </div>
    </div>
  );
}

export default StudentDashboard;
