import { BrowserRouter,HashRouter, Routes, Route } from "react-router-dom";
import StudentDashboard from "./pages/StudentDashboard";
import MyCourses from "./pages/MyCourses";
import CourseDetail from "./pages/CourseDetail";
import ChatPage from "./pages/ChatPage";
import AuthCallback from "./pages/Authcallback";


function App() {
  return (
    // <HashRouter>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<StudentDashboard />} />
        <Route path="/my-courses" element={<MyCourses />} />
        <Route path="/course/:id" element={<CourseDetail />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/callback" element={<AuthCallback />} />
      </Routes>
      </BrowserRouter>
    // </HashRouter>
  );
}


export default App;