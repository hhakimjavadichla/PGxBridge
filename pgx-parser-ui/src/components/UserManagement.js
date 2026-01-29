import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import '../styles/UserManagement.css';

function UserManagement() {
  const { token, isAdmin } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'user' });
  const [addingUser, setAddingUser] = useState(false);

  useEffect(() => {
    if (isAdmin()) {
      fetchUsers();
    }
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/auth/users', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }

      const data = await response.json();
      setUsers(data.users || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    setAddingUser(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('username', newUser.username);
      formData.append('password', newUser.password);
      formData.append('role', newUser.role);
      formData.append('authorization', `Bearer ${token}`);

      const response = await fetch('/api/auth/users', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to create user');
      }

      setNewUser({ username: '', password: '', role: 'user' });
      setShowAddUser(false);
      fetchUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setAddingUser(false);
    }
  };

  const handleDeleteUser = async (username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/auth/users/${username}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to delete user');
      }

      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleToggleUser = async (username, currentActive) => {
    try {
      const formData = new FormData();
      formData.append('active', !currentActive);
      formData.append('authorization', `Bearer ${token}`);

      const response = await fetch(`/api/auth/users/${username}/toggle`, {
        method: 'PUT',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to toggle user');
      }

      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  if (!isAdmin()) {
    return (
      <div className="user-management">
        <div className="access-denied">
          <h2>Access Denied</h2>
          <p>You need admin privileges to access this page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="user-management">
      <div className="um-header">
        <h2>User Management</h2>
        <button 
          className="add-user-btn"
          onClick={() => setShowAddUser(!showAddUser)}
        >
          {showAddUser ? 'Cancel' : '+ Add User'}
        </button>
      </div>

      {error && (
        <div className="um-error">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {showAddUser && (
        <form onSubmit={handleAddUser} className="add-user-form">
          <h3>Create New User</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                value={newUser.username}
                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                required
                placeholder="Enter username"
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                required
                placeholder="Enter password"
              />
            </div>
            <div className="form-group">
              <label>Role</label>
              <select
                value={newUser.role}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <button type="submit" className="submit-btn" disabled={addingUser}>
            {addingUser ? 'Creating...' : 'Create User'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="um-loading">Loading users...</div>
      ) : (
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Created By</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.username} className={!user.active ? 'disabled-user' : ''}>
                  <td className="username-cell">
                    {user.username}
                    {user.role === 'admin' && <span className="admin-badge">Admin</span>}
                  </td>
                  <td>{user.role}</td>
                  <td>
                    <span className={`status-badge ${user.active ? 'active' : 'inactive'}`}>
                      {user.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</td>
                  <td>{user.created_by || '-'}</td>
                  <td className="actions-cell">
                    {user.username !== 'admin' && (
                      <>
                        <button
                          className={`action-btn toggle-btn ${user.active ? 'disable' : 'enable'}`}
                          onClick={() => handleToggleUser(user.username, user.active)}
                          title={user.active ? 'Disable user' : 'Enable user'}
                        >
                          {user.active ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          className="action-btn delete-btn"
                          onClick={() => handleDeleteUser(user.username)}
                          title="Delete user"
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default UserManagement;
