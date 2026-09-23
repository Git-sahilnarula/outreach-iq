import { useState, useEffect } from 'react';
import { profileAPI } from '../services/api';
import { StartupProfile, PortfolioProject } from '../types';
import { Plus, Save } from 'lucide-react';

const Profile = () => {
  const [profile, setProfile] = useState<StartupProfile | null>(null);
  const [portfolioProjects, setPortfolioProjects] = useState<PortfolioProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAddProject, setShowAddProject] = useState(false);
  const [newProject, setNewProject] = useState({
    project_name: '',
    description: '',
    skills: '',
    technologies: '',
    portfolio_url: '',
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const [profileRes, projectsRes] = await Promise.all([
        profileAPI.getProfile(),
        profileAPI.getPortfolioProjects(),
      ]);
      setProfile(profileRes.data);
      setPortfolioProjects(projectsRes.data);
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!profile) return;
    setSaving(true);
    try {
      await profileAPI.updateProfile(profile);
      alert('Profile saved successfully!');
    } catch (error) {
      console.error('Failed to save profile:', error);
      alert('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const handleAddProject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const projectData = {
        ...newProject,
        skills: newProject.skills.split(',').map(s => s.trim()).filter(s => s),
        technologies: newProject.technologies.split(',').map(s => s.trim()).filter(s => s),
      };
      await profileAPI.addPortfolioProject(projectData);
      setNewProject({ project_name: '', description: '', skills: '', technologies: '', portfolio_url: '' });
      setShowAddProject(false);
      loadProfile();
    } catch (error) {
      console.error('Failed to add project:', error);
      alert('Failed to add project');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!profile) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Create Your Startup Profile</h2>
        <p className="text-gray-500 mb-6">Set up your profile to start analyzing job opportunities</p>
        <button
          onClick={() => setProfile({
            id: 0,
            user_id: 0,
            startup_name: '',
            remote_allowed: true,
            created_at: '',
            updated_at: '',
          })}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
        >
          Create Profile
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Startup Profile</h2>
          <p className="mt-1 text-sm text-gray-500">Manage your startup information and portfolio</p>
        </div>
        <button
          onClick={handleSaveProfile}
          disabled={saving}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Startup Name</label>
            <input
              type="text"
              value={profile.startup_name}
              onChange={(e) => setProfile({ ...profile, startup_name: e.target.value })}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              value={profile.description || ''}
              onChange={(e) => setProfile({ ...profile, description: e.target.value })}
              rows={3}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Website</label>
              <input
                type="url"
                value={profile.website || ''}
                onChange={(e) => setProfile({ ...profile, website: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Industry</label>
              <input
                type="text"
                value={profile.industry || ''}
                onChange={(e) => setProfile({ ...profile, industry: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Technical Skills (comma-separated)</label>
            <input
              type="text"
              value={profile.technical_skills?.join(', ') || ''}
              onChange={(e) => setProfile({ ...profile, technical_skills: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Python, React, Machine Learning"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Services (comma-separated)</label>
            <input
              type="text"
              value={profile.services?.join(', ') || ''}
              onChange={(e) => setProfile({ ...profile, services: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Web Development, AI Consulting, Data Analysis"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Minimum Budget</label>
              <input
                type="number"
                value={profile.minimum_budget || ''}
                onChange={(e) => setProfile({ ...profile, minimum_budget: e.target.value ? parseFloat(e.target.value) : undefined })}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Preferred Budget</label>
              <input
                type="number"
                value={profile.preferred_budget || ''}
                onChange={(e) => setProfile({ ...profile, preferred_budget: e.target.value ? parseFloat(e.target.value) : undefined })}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="remote_allowed"
              checked={profile.remote_allowed}
              onChange={(e) => setProfile({ ...profile, remote_allowed: e.target.checked })}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="remote_allowed" className="ml-2 block text-sm text-gray-900">
              Remote work allowed
            </label>
          </div>
        </div>
      </div>

      {/* Portfolio Projects */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Portfolio Projects</h3>
          <button
            onClick={() => setShowAddProject(!showAddProject)}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200"
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Project
          </button>
        </div>

        {showAddProject && (
          <form onSubmit={handleAddProject} className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Project Name</label>
                <input
                  type="text"
                  required
                  value={newProject.project_name}
                  onChange={(e) => setNewProject({ ...newProject, project_name: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  rows={2}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Skills (comma-separated)</label>
                <input
                  type="text"
                  value={newProject.skills}
                  onChange={(e) => setNewProject({ ...newProject, skills: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Technologies (comma-separated)</label>
                <input
                  type="text"
                  value={newProject.technologies}
                  onChange={(e) => setNewProject({ ...newProject, technologies: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Portfolio URL</label>
                <input
                  type="url"
                  value={newProject.portfolio_url}
                  onChange={(e) => setNewProject({ ...newProject, portfolio_url: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  Add Project
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddProject(false)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </form>
        )}

        {portfolioProjects.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No portfolio projects yet</p>
        ) : (
          <div className="space-y-4">
            {portfolioProjects.map((project) => (
              <div key={project.id} className="border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900">{project.project_name}</h4>
                <p className="text-sm text-gray-500 mt-1">{project.description}</p>
                {project.skills && project.skills.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {project.skills.map((skill, idx) => (
                      <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;
