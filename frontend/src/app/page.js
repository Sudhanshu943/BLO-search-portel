"use client";
import { useState, useEffect } from "react";
import { NewReactTransliterate } from "new-react-transliterate";
import "new-react-transliterate/styles.css"; 

export default function Home() {
  const [file, setFile] = useState(null);
  
  const [query, setQuery] = useState("");
  const [krutiQuery, setKrutiQuery] = useState(""); // Stores backend converted text
  
  const [fatherName, setFatherName] = useState("");
  const [krutiFatherName, setKrutiFatherName] = useState("");
  
  const [results, setResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [isPolling, setIsPolling] = useState(false);

  // Poll for PDF upload progress - faster polling for real-time updates
  useEffect(() => {
    let interval;
    if (isPolling) {
      interval = setInterval(async () => {
        try {
          const res = await fetch("http://localhost:8000/api/progress");
          const data = await res.json();
          setProgress(data);
          if (!data.is_processing && data.current_page > 0) setIsPolling(false);
        } catch (error) {
          console.error("Progress fetch error:", error);
        }
      }, 500); // Poll every 500ms for faster updates
    }
    return () => clearInterval(interval);
  }, [isPolling]);

  // Fetch Kruti Dev conversion for Voter Name (with debounce)
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (query) {
        try {
          // UPDATE THIS URL to match your actual backend conversion endpoint
          const res = await fetch(`http://localhost:8000/api/convert?text=${encodeURIComponent(query)}`);
          const data = await res.json();
          // Assuming backend returns {"kruti_text": "..."}
          setKrutiQuery(data.kruti_text || data.converted_text || ""); 
        } catch (error) {
          console.error("Conversion failed:", error);
        }
      } else {
        setKrutiQuery("");
      }
    }, 300); // Waits 300ms after user stops typing before calling API

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  // Fetch Kruti Dev conversion for Father's Name (with debounce)
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (fatherName) {
        try {
          // UPDATE THIS URL to match your actual backend conversion endpoint
          const res = await fetch(`http://localhost:8000/api/convert?text=${encodeURIComponent(fatherName)}`);
          const data = await res.json();
          setKrutiFatherName(data.kruti_text || data.converted_text || ""); 
        } catch (error) {
          console.error("Conversion failed:", error);
        }
      } else {
        setKrutiFatherName("");
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [fatherName]);


  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      await fetch("http://localhost:8000/api/upload", { method: "POST", body: formData });
      setIsPolling(true);
    } catch (error) {
      alert("Upload failed. Is the Python backend running?");
    }
  };

  const handleSearch = async () => {
    if (!query) return;
    setSearchLoading(true);
    try {
      // Search: query in name column, fatherName in relative column
      const res = await fetch(`http://localhost:8000/api/search?query=${query}&relative_name=${fatherName}`);
      const data = await res.json();
      setResults(data);
    } catch (error) {
      console.error("Search failed", error);
    }
    setSearchLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8 font-sans text-gray-900">
      <div className="max-w-5xl mx-auto bg-white p-8 rounded-xl shadow-lg border border-gray-200">
        <h1 className="text-3xl font-bold mb-8 text-center text-blue-700">PDF Name Finder</h1>
        
        {/* Step 1: Upload */}
        <div className="mb-8 p-6 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
          <h2 className="text-xl font-semibold mb-4">1. Process PDF Database</h2>
          <div className="flex flex-col sm:flex-row gap-4">
            <input 
              type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files[0])}
              className="block w-full text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <button 
              onClick={handleUpload} disabled={isPolling || !file}
              className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400 font-semibold"
            >
              {isPolling ? "Processing..." : "Extract Database"}
            </button>
          </div>
          
          {progress && (
            <div className="mt-4 p-4 bg-white border rounded shadow-sm">
              <p className="text-sm font-semibold mb-2">{progress.message}</p>
              {progress.total_pages > 0 && (
                <>
                  <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                    <div className="bg-blue-600 h-3 rounded-full transition-all" style={{ width: `${(progress.current_page / progress.total_pages) * 100}%` }}></div>
                  </div>
                  <div className="flex flex-wrap gap-4 text-xs text-gray-600">
                    <span className="bg-gray-100 px-2 py-1 rounded">
                      Page: {progress.current_page} / {progress.total_pages}
                    </span>
                    {progress.pages_per_second > 0 && (
                      <span className="bg-green-100 px-2 py-1 rounded text-green-700">
                        Speed: {progress.pages_per_second.toFixed(2)} pages/sec
                      </span>
                    )}
                    {progress.estimated_time_remaining > 0 && (
                      <span className="bg-orange-100 px-2 py-1 rounded text-orange-700">
                        ETA: {Math.floor(progress.estimated_time_remaining / 60)}m {Math.round(progress.estimated_time_remaining % 60)}s remaining
                      </span>
                    )}
                    {progress.download_speed > 0 && (
                      <span className="bg-blue-100 px-2 py-1 rounded text-blue-700">
                        Records: {progress.download_speed.toFixed(1)} rec/sec
                      </span>
                    )}
                    {progress.records_extracted > 0 && (
                      <span className="bg-purple-100 px-2 py-1 rounded text-purple-700">
                        Total: {progress.records_extracted} records
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Step 2: Search */}
        <div className="mb-8 p-6 border rounded-lg bg-white shadow-sm">
          <h2 className="text-xl font-semibold mb-2">2. Search Names</h2>
          <p className="text-xs text-gray-500 mb-4 italic">Type in English (e.g. "pankaj") and press Space to convert to Hindi.</p>
          <div className="flex flex-col md:flex-row gap-4 items-start">
            
            <div className="flex-1 w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Voter Name (Required)</label>
              <NewReactTransliterate
                value={query} onChangeText={setQuery} lang="hi"
                renderComponent={(props) => <input {...props} className="border p-3 rounded w-full focus:outline-none focus:border-blue-500" placeholder="e.g. पंकज" />}
              />
              {/* Backend Kruti Dev Output for Voter Name */}
              {krutiQuery && (
                <div className="mt-2 p-2 bg-blue-50 border border-blue-100 rounded text-center">
                  <span className="text-xs text-blue-500 block mb-1 uppercase font-semibold tracking-wider">Kruti Dev Preview</span>
                  <span className="text-2xl text-gray-800" style={{ fontFamily: 'KrutiDev, sans-serif' }}>
                    {krutiQuery}
                  </span>
                </div>
              )}
            </div>

            <div className="flex-1 w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Father's Name (Optional)</label>
              <NewReactTransliterate
                value={fatherName} onChangeText={setFatherName} lang="hi"
                renderComponent={(props) => <input {...props} className="border p-3 rounded w-full focus:outline-none focus:border-blue-500" placeholder="e.g. रमेश" />}
              />
              {/* Backend Kruti Dev Output for Father's Name */}
              {krutiFatherName && (
                <div className="mt-2 p-2 bg-blue-50 border border-blue-100 rounded text-center">
                  <span className="text-xs text-blue-500 block mb-1 uppercase font-semibold tracking-wider">Kruti Dev Preview</span>
                  <span className="text-2xl text-gray-800" style={{ fontFamily: 'KrutiDev, sans-serif' }}>
                    {krutiFatherName}
                  </span>
                </div>
              )}
            </div>

            <div className="flex items-end mt-6 md:mt-0">
              <button onClick={handleSearch} disabled={searchLoading || !query} className="bg-green-600 text-white px-8 py-3 rounded hover:bg-green-700 disabled:bg-gray-400 font-bold h-[50px] w-full md:w-auto">
                {searchLoading ? "Searching..." : "Search"}
              </button>
            </div>
          </div>
        </div>

        {/* Step 3: Results */}
        {results && (
          <div className="mt-8 border-t pt-8">
            <h3 className="text-xl font-bold mb-4">Found <span className="text-green-600">{results.total_matches}</span> matches</h3>
            {results.results?.length > 0 ? (
              <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                {results.results.map((res, index) => (
                  <div key={index} className="p-5 bg-white rounded-xl border shadow-sm hover:shadow-md">
                    <span className="text-xs font-bold text-white bg-blue-600 px-3 py-1 rounded-full uppercase tracking-wider mb-4 inline-block">Page {res.page_number}</span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
                        <p className="text-xs text-blue-500 font-semibold uppercase mb-1">निर्वाचक का नाम (Voter)</p>
                        <p className="text-2xl font-bold">{res.voter_name || res.name || "N/A"}</p>
                        {res.serial_number && <p className="text-xs text-gray-500">S.No: {res.serial_number}</p>}
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg border border-green-100">
                        <p className="text-xs text-green-600 font-semibold uppercase mb-1">पिता/पति का नाम (Father/Husband)</p>
                        <p className="text-2xl font-bold">{res.father_name || res.relative_name || "N/A"}</p>
                        {res.relation && <p className="text-xs text-gray-500">Relation: {res.relation}</p>}
                      </div>
                    </div>
                    {(res.age || res.gender || res.voter_id) && (
                      <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-600">
                        {res.age && <span className="bg-gray-100 px-2 py-1 rounded">Age: {res.age}</span>}
                        {res.gender && <span className="bg-gray-100 px-2 py-1 rounded">Gender: {res.gender}</span>}
                        {res.voter_id && <span className="bg-gray-100 px-2 py-1 rounded">ID: {res.voter_id}</span>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 bg-gray-50 p-4 rounded text-center">No matches found.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}