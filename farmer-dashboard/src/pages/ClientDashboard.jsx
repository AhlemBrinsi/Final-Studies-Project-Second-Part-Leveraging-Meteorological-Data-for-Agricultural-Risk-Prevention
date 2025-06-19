import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ClientProfile from './ClientProfile.jsx'; 
//import DashboardMain from './DashboardMain.jsx';
import { useLocation } from 'react-router-dom';
import ViewArticles from './ViewArticles.jsx';
import ClientSupport from './ClientSupport.jsx';
import ClientWeatherDashboard from './ClientWeatherDashboard.jsx';
export default function ClientDashboard() {
  const [searchOpen, setSearchOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();
  const [activeView, setActiveView] = useState("weather");


  // ✅ Handle missing user data (page refresh case)
  const { state } = useLocation();
  const user = state?.user; // Gets user data from navigation state
  const handleLogout = () => {
    //localStorage.removeItem('user'); // Clear saved user data
    navigate('/'); // Redirect to login
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-200">
      {/* Top Bar */}
      <header className="w-full flex items-center justify-between px-6 py-4 bg-gray-200">
        <span className="font-bold text-2xl text-gray-800">Farmer Space</span>

        <div className="flex items-center space-x-4 relative">
          {!searchOpen ? (
            <button
              onClick={() => setSearchOpen(true)}
              className="text-gray-600 hover:text-gray-800 bg-transparent p-0 border-0"
              aria-label="Open search"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </button>
          ) : (
            <input
              type="text"
              placeholder="Search..."
              autoFocus
              onBlur={() => setSearchOpen(false)}
              className="border-b-2 border-gray-400 focus:border-green-600 bg-transparent text-gray-900 placeholder-gray-400 focus:outline-none px-2 py-1 w-48"
            />
          )}

           {/* Profile + Dropdown */}
          <div ref={dropdownRef} className="relative">
            <img
              src="ava.jpg" 
              alt="Avatar" 
              style={{ width: '50px', height: '50px', borderRadius: '50%' }} 
              onClick={() => setDropdownOpen(!dropdownOpen)}
            />
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-40 rounded-md shadow-lg z-10">
              <button
                onClick={() => {
                  setActiveView("profile");
                  setDropdownOpen(false); // Optional: close the dropdown after clicking
                }}
                className="hover:opacity-100 flex items-center px-2 space-x-2 w-full text-left"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
                  />
                </svg>
                <span>Profile</span>
              </button>
              <button
                onClick={handleLogout}
                className="hover:opacity-100 flex items-center px-2 space-x-2 w-full text-left"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="size-6">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 9V5.25A2.25 2.25 0 0 1 10.5 3h6a2.25 2.25 0 0 1 2.25 2.25v13.5A2.25 2.25 0 0 1 16.5 21h-6a2.25 2.25 0 0 1-2.25-2.25V15m-3 0-3-3m0 0 3-3m-3 3H15" />
                </svg>
                <span>Logout</span>
              </button>
              </div>
              )}

          </div>
        </div>
      </header>

      {/* Main Section: Sidebar + Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-50 min-h-[calc(80vh-10px)] mb-10 bg-gradient-to-tr from-green-400 to-green-500 text-white flex flex-col p-6 rounded-lg shadow-lg transition-all duration-300 hover:w-60 ml-4 items-start">
          {/* Top nav items */}
          <nav className="flex flex-col space-y-10 text-sm opacity-80 w-full">
            <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setActiveView("weather");
                  setDropdownOpen(false);
                }}
                className="hover:opacity-100 block px-2 flex items-center space-x-2"
            >
              {/* Weather icon */}
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15a4.5 4.5 0 0 0 4.5 4.5H18a3.75 3.75 0 0 0 1.332-7.257 3 3 0 0 0-3.758-3.848 5.25 5.25 0 0 0-10.233 2.33A4.502 4.502 0 0 0 2.25 15Z" />
              </svg>

              <span>Weather</span>
            </a>

            <a href="#" className="hover:opacity-100 block px-2 flex items-center space-x-3">
              {/* Notifications icon */}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span>Notifications</span>
            </a>

            <a href="#" className="hover:opacity-100 block px-2 flex items-center space-x-3">
              {/* Recommendations icon */}
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z" />
              </svg>

              <span>Recommandations</span>
            </a>

            <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setActiveView("view-articles");
                  setDropdownOpen(false);
                }}
                className="hover:opacity-100 block px-2 flex items-center space-x-2"
            >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                  />
                </svg>
              <span>Articles</span>
            </a>
            <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setActiveView("support");
                  setDropdownOpen(false);
                }}
                className="hover:opacity-100 block px-2 flex items-center space-x-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="size-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
              </svg>

              <span> Support</span>
            </a>


            <a href="#" className="hover:opacity-100 block px-2 flex items-center space-x-3">
              {/* Voice Assistant icon */}
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
                />
              </svg>
              <span>Voice Assistant</span>
            </a>
          </nav>
        </aside>


        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 p-6 overflow-auto">
            {activeView === "profile" && (
                <div className="bg-gray-100 rounded-lg p-4 shadow mb-6">
                      <ClientProfile user={user} />
                </div>
            )}
            {activeView === "view-articles" && (
                <div className="bg-gray-100 rounded-lg p-4 shadow mb-6">
                      <ViewArticles />
                </div>
            )}
            {activeView === "support" && (
                <div className="bg-gray-100 rounded-lg p-4 shadow mb-6">
                      <ClientSupport />
                </div>
            )}
            {activeView === "weather" && (
                <div className="bg-gray-100 rounded-lg p-4 shadow mb-6">
                      <ClientWeatherDashboard />
                </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
} 