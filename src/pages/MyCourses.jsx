import { useState } from "react";
import { Search, Brain, BarChart3, Code } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/SideBar";
import Header from "../components/Header";
import { courses } from "../data/courses";
import CourseCard from "../components/CourseCard";

function MyCourses() {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const filteredCourses = courses.filter(c =>
    c.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <Sidebar />

      <div className="main-content">
        {/* Header */}
        <Header />

        {/* Page title + search */}
        <div className="courses-header">
          <h2>My Courses ({filteredCourses.length})</h2>

          <div className="course-actions">
            <div className="search-box">
              <Search size={16} />
              <input
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Course cards */}
        {/* map -> is loop thatb runs every course */}
        {/* {...course} -> Take everything inside course and send it to the component. So, You don’t have to write each prop one by one*/}
        <div className="course-grid">
          {filteredCourses.map(course => (
            <CourseCard key={course.id} {...course} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default MyCourses;

