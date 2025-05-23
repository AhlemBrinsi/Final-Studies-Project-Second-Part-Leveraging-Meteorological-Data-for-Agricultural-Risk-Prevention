import React,{ useState, useEffect } from "react";
import axios from "axios";

export default function OwnerProfile({ user }) {

const [profile, setProfile] = useState(user || { 
    id: '',
    username: '',
    email: '',
    role: '',
    age: '',
    job: '',
    bio: '',
    profilePicture: ''
  });

const [isEditing, setIsEditing] = useState(false);
const [profilePicFile, setProfilePicFile] = useState(null);
const [hasChanged, setHasChanged] = useState(false);
const [originalProfile, setOriginalProfile] = useState(null);
const [loading, setLoading] = useState(true);
  //const [setLoading] = useState(false);

useEffect(() => {
  const fetchProfile = async () => {
    try {
      const userData = JSON.parse(localStorage.getItem('user')) || {};
      const userId = userData.id || userData._id;

      if (!userId) {
        console.error("No ID found in user data");
        return;
      }

      const response = await axios.get(`http://localhost:5000/api/users/${userId}`);
      setProfile(response.data);
      setOriginalProfile(response.data); // Save original profile for cancel
    } catch (err) {
      console.error("Failed to fetch profile:", err);
    } finally {
      setLoading(false);
    }
  };

  fetchProfile();
}, []);

const handleCancel = () => {
  setProfile(originalProfile); // Revert to original
  setIsEditing(false);
  setHasChanged(false);
  setProfilePicFile(null);
};




const handleFileChange = (e) => {
  if (e.target.files && e.target.files[0]) {
    setProfilePicFile(e.target.files[0]);
    
    // Optionally preview the image locally:
    const reader = new FileReader();
    reader.onload = () => {
      setProfile(prev => ({ ...prev, profilePicture: reader.result }));
    };
    reader.readAsDataURL(e.target.files[0]);
  }
  setHasChanged(true);
};


  // Input change
const handleChange = (e) => {
  setProfile({ ...profile, [e.target.name]: e.target.value });
  setHasChanged(true);
};


const handleSubmit = async (e) => {
  e.preventDefault();
  const userData = JSON.parse(localStorage.getItem('user')) || {};
  const userId = userData.id || userData._id;

  if (!userId) {
    console.error("No user ID found.");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("username", profile.username);
    formData.append("email", profile.email);
    formData.append("age", profile.age);
    formData.append("job", profile.job);
    formData.append("bio", profile.bio);
    

    if (profilePicFile) {
      formData.append("profilePicture", profilePicFile);
    }

    const response = await axios.put(
      `http://localhost:5000/api/users/${userId}`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    setProfile(response.data.user); // update UI with latest data
    setIsEditing(false);
    setHasChanged(false);
    alert("Profile updated successfully!");
  } catch (err) {
    console.error("Error updating profile:", err);
    alert("Failed to update profile.");
  }
};


return (
    <div className="max-w-3xl mx-auto p-6 bg-white shadow-md rounded-xl mt-10">
      <h2 className="text-2xl font-semibold mb-4">Profile</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Profile Picture */}
        <div className="flex items-center space-x-4 mb-4">
          <img
            src={
              profile.profilePicture
                ? profile.profilePicture.startsWith("/uploads")
                  ? `http://localhost:5000${profile.profilePicture}`
                  : profile.profilePicture
                : "/ava.jpg"
            }
            alt="Profile"
            className="w-20 h-20 rounded-full object-cover"
          />
          {isEditing && (
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="text-sm"
            />
          )}
        </div>

        {/* Username */}
        <div>
          <label className="block text-sm font-medium">Name</label>
          <input
            type="text"
            name="username"
            value={profile.username}
            onChange={handleChange}
            readOnly={!isEditing}
            className="w-full mt-1 p-2 border border-gray-300 rounded-md"
          />
        </div>

        {/* Email */}
        <div>
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            name="email"
            value={profile.email}
            onChange={handleChange}
            readOnly={!isEditing}
            className="w-full mt-1 p-2 border border-gray-300 rounded-md"
          />
        </div>
        {/* Age */}
        <div>
          <label className="block text-sm font-medium">Age</label>
          <input
            type="age"
            name="age"
            value={profile.age}
            onChange={handleChange}
            readOnly={!isEditing}
            className="w-full mt-1 p-2 border border-gray-300 rounded-md"
          />
        </div>

        {/* Role */}
        <div>
          <label className="block text-sm font-medium">Role</label>
          <input
            type="text"
            name="role"
            value={profile.role}
            readOnly
            className="w-full mt-1 p-2 border border-gray-200 bg-gray-100 rounded-md"
          />
        </div>

        {/* Job */}
        <div>
          <label className="block text-sm font-medium">Job</label>
          <select
            name="job"
            value={profile.job}
            onChange={handleChange}
            disabled={!isEditing}
            className="w-full mt-1 p-2 border border-gray-300 rounded-md"
          >
            <option value="">Select Job</option>
            <option value="Director">Director</option>
            <option value="Boss">Boss</option>
            <option value="Data Scientist">Data Scientist</option>
            <option value="Data Analyst">Data Analyst</option>
            <option value="Data Engineer">Data Engineer</option>
            <option value="Project Manager">Project Manager</option>
            <option value="Developer">Developer</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {/* Bio */}
        <div>
          <label className="block text-sm font-medium">Bio</label>
          <textarea
            name="bio"
            value={profile.bio}
            onChange={handleChange}
            readOnly={!isEditing}
            className="w-full mt-1 p-2 border border-gray-300 rounded-md"
            rows={4}
          />
        </div>

        {/* Buttons */}
        {!isEditing ? (
            <button
              type="button"
              onClick={() => {
                setIsEditing(true);
                setOriginalProfile(profile); // Save current profile in case user cancels
              }}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition"
            >
              Edit Profile
            </button>
          ) : (
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={!hasChanged}
                className={`px-6 py-2 rounded transition text-white ${
                  hasChanged
                    ? "bg-green-600 hover:bg-green-700"
                    : "bg-gray-400 cursor-not-allowed"
                }`}
              >
                Save Changes
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="bg-red-500 text-white px-6 py-2 rounded hover:bg-red-600 transition"
              >
                Cancel Changes
              </button>
            </div>
          )}

      </form>
    </div>
);
}
