import { useState, useEffect } from "react";
import { Plus, Building2, Mail, MapPin, Briefcase } from "lucide-react";
import { api } from "../services/api";

interface University {
  email: string;
  country: string;
  verification_department: string;
}

export default function UniversitiesTab() {
  const [universities, setUniversities] = useState<Record<string, University>>({});
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [country, setCountry] = useState("");
  const [department, setDepartment] = useState("");

  useEffect(() => {
    loadUniversities();
  }, []);

  const loadUniversities = async () => {
    try {
      setLoading(true);
      const data = await api.getUniversities();
      setUniversities(data);
    } catch (err) {
      console.error("Failed to load universities:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;

    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setError("Please enter a valid email address");
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await api.addUniversity(name.trim(), email.trim(), country.trim(), department.trim());
      
      // Reset form
      setName("");
      setEmail("");
      setCountry("");
      setDepartment("");
      setShowForm(false);
      
      // Reload list
      await loadUniversities();
    } catch (err: any) {
      setError(err.message || "Failed to add university");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Universities</h2>
          <p className="text-sm text-slate-500 mt-1">
            Add custom universities to test with your own data
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add University
        </button>
      </div>

      {/* Info Note */}
      <div className="text-xs text-slate-400 bg-slate-50 rounded-lg px-3 py-2">
        💡 Simple utility to add universities to config for testing purposes.
      </div>

      {/* Add Form */}
      {showForm && (
        <div className="glass-card rounded-xl p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Add New University</h3>
          
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  University Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Harvard University"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g., verify@university.edu"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Country
                </label>
                <input
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="e.g., USA"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Verification Department
                </label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="e.g., Office of the Registrar"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={saving || !name.trim() || !email.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {saving ? "Adding..." : "Add University"}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-slate-600 hover:text-slate-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* University List */}
      <div className="glass-card rounded-xl p-6">
        {loading ? (
          <div className="text-center py-8 text-slate-500">Loading...</div>
        ) : Object.keys(universities).length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            No universities configured. Add one to get started.
          </div>
        ) : (
          <div className="grid gap-4">
            {Object.entries(universities).map(([uniName, info]) => (
              <div
                key={uniName}
                className="flex items-start gap-4 p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Building2 className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-slate-800">{uniName}</h4>
                  <div className="mt-1 space-y-1 text-sm text-slate-600">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      <span>{info.email}</span>
                    </div>
                    {info.country && (
                      <div className="flex items-center gap-2">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{info.country}</span>
                      </div>
                    )}
                    {info.verification_department && (
                      <div className="flex items-center gap-2">
                        <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                        <span>{info.verification_department}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        <div className="mt-4 pt-4 border-t border-slate-200 text-xs text-slate-400">
          Total: {Object.keys(universities).length} universities
        </div>
      </div>
    </div>
  );
}
