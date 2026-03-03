import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import ImageOverlay from "../components/ImageOverlay";
import type {
  SegmentResult,
  ClassificationResult,
  PreviewFile,
} from "../types";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const API_URL = "http://127.0.0.1:8000";

  
  const [previews, setPreviews] = useState<PreviewFile[]>([]);
  const [segResults, setSegResults] = useState<SegmentResult[]>([]);
  const [clsResults, setClsResults] = useState<ClassificationResult | null>(
    null
  );


  const [isSegmenting, setIsSegmenting] = useState<boolean>(false);
  const [isClassifying, setIsClassifying] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);

  
  const [showCoarse, setShowCoarse] = useState<boolean>(true);
  const [showLesion, setShowLesion] = useState<boolean>(true);

  const getAuthHeaders = (): Record<string, string> => {
    const token = localStorage.getItem('access_token');
    if (token) {
        return { 'Authorization': `Bearer ${token}` };
    }
    return {};
  };


  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    
    setSegResults([]);
    setClsResults(null);
    setError(null);

    const sortedFiles = Array.from(files).sort((a, b) =>
      a.name.localeCompare(b.name, undefined, {
        numeric: true,
        sensitivity: "base",
      })
    );

    const initialPreviews: PreviewFile[] = sortedFiles.map((f) => ({
      name: f.name,
      url: f.type.startsWith("image/") ? URL.createObjectURL(f) : null,
      file: f,
      isLoadingPreview: !f.type.startsWith("image/"),
      isGeneratingCaption: false,
    }));

    setPreviews(initialPreviews);

    
    const dcmFiles = initialPreviews.filter((p) => p.isLoadingPreview);
    const previewPromises = dcmFiles.map((dcmPreview) => {
      const formData = new FormData();
      formData.append("file", dcmPreview.file);
      return fetch(`${API_URL}/preview_dcm`, { method: "POST", body: formData })
        .then((res) => res.json())
        .then((data) => ({ name: dcmPreview.name, data }))
        .catch((err) => ({ name: dcmPreview.name, error: err }));
    });

    const results = await Promise.all(previewPromises);

    setPreviews((currentPreviews) => {
      const updatedPreviews = [...currentPreviews];
      results.forEach((result) => {
        const res = result as { name: string; data?: any; error?: any };
        const index = updatedPreviews.findIndex((p) => p.name === res.name);
        if (index !== -1) {
          updatedPreviews[index] = {
            ...updatedPreviews[index],
            isLoadingPreview: false,
            url: res.data && res.data.success ? res.data.png_base64 : null,
          };
        }
      });
      return updatedPreviews;
    });
  };

 
  const handleSegmentation = async () => {
    if (previews.length === 0) return;
    setIsSegmenting(true);

    
    if (error) setError(null);

    const formData = new FormData();
    previews.forEach((p) => formData.append("files", p.file, p.name));

    try {
      const res = await fetch(`${API_URL}/run_segmentation`, {
        method: "POST",
        headers: {
            ...getAuthHeaders() 
        },
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setSegResults(data.results);
      } else {
        throw new Error(data.error);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsSegmenting(false);
    }
  };


  const handleClassification = async () => {
    if (previews.length === 0) return;
    setIsClassifying(true);

    if (error) setError(null);

    const formData = new FormData();
    try {
      for (const preview of previews) {
        formData.append("original_files", preview.file, preview.name);
      }
      const res = await fetch(`${API_URL}/run_classification`, {
        method: "POST",
        headers: {
            ...getAuthHeaders() 
        },
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setClsResults({ diagnosis: data.patient_diagnosis, details: [] });
      } else {
        throw new Error(data.error);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsClassifying(false);
    }
  };




  const generateCaptionForFile = async (preview: PreviewFile) => {
    const formData = new FormData();
    formData.append("file", preview.file);
    try {
      const res = await fetch(`${API_URL}/generate_caption`, {
        method: "POST",
        headers: {
            ...getAuthHeaders() 
        },
        body: formData,
      });
      const data = await res.json();
      return data.success ? data.caption : "Lỗi";
    } catch (e) {
      return "Lỗi kết nối";
    }
  };

  const handleSingleCaption = async (previewName: string) => {
    setPreviews((prev) =>
      prev.map((p) =>
        p.name === previewName ? { ...p, isGeneratingCaption: true } : p
      )
    );
    const preview = previews.find((p) => p.name === previewName);
    if (preview) {
      const caption = await generateCaptionForFile(preview);
      setPreviews((prev) =>
        prev.map((p) =>
          p.name === previewName
            ? { ...p, isGeneratingCaption: false, caption }
            : p
        )
      );
    }
  };

  const handleBatchCaption = async () => {
    
    const newPreviews = [...previews];
    for (let i = 0; i < newPreviews.length; i++) {
      if (!newPreviews[i].caption) {
        setPreviews((prev) =>
          prev.map((p, idx) =>
            idx === i ? { ...p, isGeneratingCaption: true } : p
          )
        );
        const cap = await generateCaptionForFile(newPreviews[i]);
        setPreviews((prev) =>
          prev.map((p, idx) =>
            idx === i ? { ...p, isGeneratingCaption: false, caption: cap } : p
          )
        );
      }
    }
  };

  const getLabelColor = (label: string) => {
    if (label.includes("Normal")) return "text-green-400 border-green-400";
    if (label.includes("Adenocarcinoma")) return "text-red-400 border-red-400";
    return "text-yellow-400 border-yellow-400";
  };

 
  return (
    <div className="min-h-screen bg-[#0f172a] text-gray-200 font-sans p-6">
     
      <div className="max-w-7xl mx-auto mb-8 border-b border-gray-700 pb-4 flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
            HỆ THỐNG CHẨN ĐOÁN UNG THƯ PHỔI
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Phân Vùng • Phân Loại • Mô Tả
          </p>
        </div>

        <div className="flex items-center gap-4 bg-gray-800/60 py-2 px-4 rounded-full border border-gray-700">
          <div className="text-right hidden sm:block">
            <div className="text-sm font-bold text-gray-200">{user?.name}</div>
            <div className="text-[10px] text-cyan-400 tracking-wider">
              {user?.email}
            </div>
          </div>
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-bold border-2 border-gray-600 shadow-md">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <button
            onClick={logout}
            className="ml-2 text-xs bg-red-500/10 hover:bg-red-500/30 text-red-400 px-3 py-1.5 rounded-full border border-red-500/30 transition-all"
          >
            Đăng xuất
          </button>
        </div>
      </div>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CỘT TRÁI: ĐIỀU KHIỂN */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-gray-800/50 p-5 rounded-xl border border-gray-700 shadow-lg">
            {/* Input File */}
            <label className="block mb-6 group cursor-pointer">
              <span className="text-sm font-semibold text-gray-400 mb-2 block group-hover:text-cyan-400 transition-colors">
                📂 Chọn thư mục bệnh nhân
              </span>
              <input
                type="file"
                multiple
                webkitdirectory=""
                onChange={handleFileChange}
                className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-violet-600 file:text-white hover:file:bg-violet-700 cursor-pointer"
                {...({ webkitdirectory: "" } as any)}
              />
            </label>

            
            <div className="grid grid-cols-2 gap-3 mb-3">
              
              <button
                onClick={handleSegmentation}
                disabled={isSegmenting || previews.length === 0}
                className={`py-3 rounded-lg font-bold text-xs transition-all flex flex-col items-center justify-center gap-1 border border-transparent
                    ${
                      isSegmenting
                        ? "bg-gray-700 cursor-wait"
                        : previews.length > 0
                        ? "bg-blue-900/40 hover:bg-blue-800/60 text-blue-200 border-blue-800"
                        : "bg-gray-800 text-gray-600 cursor-not-allowed"
                    }
                  `}
              >
                <span>{isSegmenting ? "Đang chạy..." : "Phân vùng"}</span>
              </button>

              
              <button
                onClick={handleClassification}
                disabled={isClassifying || previews.length === 0}
                className={`py-3 rounded-lg font-bold text-xs transition-all flex flex-col items-center justify-center gap-1 border border-transparent
                    ${
                      isClassifying
                        ? "bg-gray-700 cursor-wait"
                        : previews.length > 0
                        ? "bg-emerald-900/40 hover:bg-emerald-800/60 text-emerald-200 border-emerald-800"
                        : "bg-gray-800 text-gray-600 cursor-not-allowed"
                    }
                  `}
              >
                <span>{isClassifying ? "Đang chạy..." : "Phân loại"}</span>
              </button>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-900/30 text-red-300 text-xs rounded border border-red-800">
                {error}
              </div>
            )}
          </div>

          
          {clsResults?.diagnosis && (
            <div className="bg-gradient-to-br from-gray-800 to-slate-900 p-5 rounded-xl border border-blue-500/30 shadow-xl animate-fade-in">
              <h3 className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">
                KẾT QUẢ CHẨN ĐOÁN
              </h3>
              <div
                className={`text-2xl font-extrabold ${
                  getLabelColor(clsResults.diagnosis.final_label).split(" ")[0]
                }`}
              >
                {clsResults.diagnosis.final_label}
              </div>
              <div className="text-sm text-gray-300 mt-1">
                Độ tin cậy:{" "}
                <b className="text-white">
                  {clsResults.diagnosis.final_confidence}%
                </b>
              </div>
              <div className="mt-4 space-y-2">
                {Object.entries(clsResults.diagnosis.mean_probs).map(
                  ([label, prob]) => (
                    <div
                      key={label}
                      className="flex justify-between items-center text-xs"
                    >
                      <span className="text-gray-500">{label}</span>
                      <div className="flex items-center gap-2 w-1/2">
                        <div className="h-1.5 bg-gray-700 rounded-full flex-1 overflow-hidden">
                          <div
                            className={`h-full ${
                              label === clsResults.diagnosis?.final_label
                                ? "bg-blue-500"
                                : "bg-gray-600"
                            }`}
                            style={{ width: `${prob}%` }}
                          ></div>
                        </div>
                        <span className="w-8 text-right text-gray-400">
                          {prob}%
                        </span>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
        </div>

        
        <div className="lg:col-span-2 bg-gray-900 rounded-xl border border-gray-800 flex flex-col h-[85vh]">
          <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-800/50 rounded-t-xl sticky top-0 z-40 backdrop-blur-sm">
            <h3 className="font-semibold text-gray-300 flex items-center gap-2">
              Danh sách lát cắt{" "}
              <span className="bg-gray-700 text-white text-[10px] px-2 py-0.5 rounded-full">
                {previews.length}
              </span>
            </h3>

            <div className="flex gap-3">
              
              {segResults.length > 0 && (
                <div className="flex items-center gap-2 bg-gray-800 px-3 py-1 rounded-full border border-gray-700 animate-fade-in">
                  <span className="text-[10px] text-gray-500 uppercase font-bold mr-1">
                    Hiển Thị:
                  </span>
                  <button
                    onClick={() => setShowCoarse(!showCoarse)}
                    className={`text-xs px-2 py-1 rounded transition-all ${
                      showCoarse
                        ? "bg-cyan-900/40 text-cyan-300 border border-cyan-700"
                        : "text-gray-500"
                    }`}
                  >
                    Elip
                  </button>
                  <button
                    onClick={() => setShowLesion(!showLesion)}
                    className={`text-xs px-2 py-1 rounded transition-all ${
                      showLesion
                        ? "bg-red-900/40 text-red-300 border border-red-700"
                        : "text-gray-500"
                    }`}
                  >
                    Chi Tiết
                  </button>
                </div>
              )}
              {previews.length > 0 && (
                <button
                  onClick={handleBatchCaption}
                  className="text-xs bg-purple-600 hover:bg-purple-500 text-white px-3 py-1.5 rounded-full font-semibold shadow-lg"
                >
                  Mổ tả toàn bộ
                </button>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {previews.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-50">
                <span className="text-4xl mb-2">📁</span>
                <p className="text-sm">Vui lòng tải lên thư mục ảnh CT</p>
              </div>
            ) : (
              previews.map((preview) => {
                const seg = segResults.find((r) => r.filename === preview.name);
                return (
                  <div
                    key={preview.name}
                    className="flex flex-col sm:flex-row gap-4 bg-gray-800/40 p-3 rounded-lg border border-gray-700/50 hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex-shrink-0">
                      
                      <ImageOverlay
                        originalUrl={preview.url}
                        maskCoarse={seg?.mask_coarse}
                        maskLesion={seg?.mask_lesion}
                        showCoarse={showCoarse}
                        showLesion={showLesion}
                      />
                      <div className="text-center mt-2 text-[10px] text-gray-500 truncate w-48 font-mono">
                        {preview.name}
                      </div>
                    </div>
                    <div className="flex-1 flex flex-col gap-2">
                      <div className="flex-1 bg-black/20 rounded p-3 border border-gray-700/50 relative">
                        <div className="text-xs text-purple-400 font-bold mb-1 flex justify-between items-center">
                          <span>PHÂN TÍCH AI:</span>
                          {!preview.caption && (
                            <button
                              onClick={() => handleSingleCaption(preview.name)}
                              className="text-[10px] text-gray-500 hover:text-white underline"
                            >
                              {preview.isGeneratingCaption
                                ? "Running..."
                                : "Phân tích ảnh này"}
                            </button>
                          )}
                        </div>
                        {preview.isGeneratingCaption ? (
                          <div className="text-xs text-gray-500 animate-pulse mt-2">
                            Đang tạo mô tả...
                          </div>
                        ) : preview.caption ? (
                          <p className="text-sm text-gray-300 italic mt-1 leading-relaxed">
                            "{preview.caption}"
                          </p>
                        ) : (
                          <p className="text-xs text-gray-600 italic mt-1">
                            Chưa có mô tả chi tiết.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
