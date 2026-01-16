import { HashRouter, Routes, Route } from "react-router-dom";
import StudentDashboard from "./pages/StudentDashboard";
import MyCourses from "./pages/MyCourses";
import CourseDetail from "./pages/CourseDetail";
import ChatPage from "./pages/ChatPage";

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<StudentDashboard />} />
        <Route path="/my-courses" element={<MyCourses />} />
        <Route path="/course/:id" element={<CourseDetail />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </HashRouter>
  );
}


export default App;