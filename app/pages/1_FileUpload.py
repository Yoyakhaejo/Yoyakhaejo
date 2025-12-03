import streamlit as st

import React, { useState, createContext, useContext, useRef, useEffect } from 'react';
import { 
  Upload, FileText, Youtube, Type, CheckCircle, 
  MessageSquare, BookOpen, Menu, X, ArrowRight, 
  FileVideo, Loader2 
} from 'lucide-react';

/**
 * [전역 상태 관리 - Context API]
 * * 실제 팀 프로젝트에서 가장 중요한 부분입니다.
 * 업로드한 데이터를 이 Context에 저장함으로써,
 * 페이지가 바뀌어도(예: 업로드 -> 노트생성) 데이터가 유지됩니다.
 */
const ProjectContext = createContext();

const ProjectProvider = ({ children }) => {
  // 현재 프로젝트 상태 (업로드된 파일 정보, 처리 상태 등)
  const [projectData, setProjectData] = useState({
    isLoaded: false,      // 데이터가 있는지 여부
    type: null,           // 'file', 'youtube', 'text'
    fileName: '',         // 파일명 또는 영상 제목
    content: null,        // 실제 파일 객체 또는 텍스트/URL
    summary: null,        // (나중에 생성될) 요약본
    quiz: null,           // (나중에 생성될) 퀴즈
    uploadDate: null,
  });

  // 데이터를 업데이트하는 함수
  const updateProjectData = (data) => {
    setProjectData((prev) => ({ ...prev, ...data }));
  };

  // 데이터 초기화 (새 파일 업로드 시)
  const resetProjectData = () => {
    setProjectData({
      isLoaded: false,
      type: null,
      fileName: '',
      content: null,
      summary: null,
      quiz: null,
      uploadDate: null,
    });
  };

  return (
    <ProjectContext.Provider value={{ projectData, updateProjectData, resetProjectData }}>
      {children}
    </ProjectContext.Provider>
  );
};

// Custom Hook for using context easier
const useProject = () => useContext(ProjectContext);


/**
 * [UI 컴포넌트: 사이드바]
 * 페이지 이동 네비게이션
 */
const Sidebar = ({ activePage, setActivePage, isMobileOpen, setIsMobileOpen }) => {
  const { projectData } = useProject();

  const menuItems = [
    { id: 'upload', label: '자료 업로드', icon: Upload },
    { id: 'notes', label: '강의 노트', icon: BookOpen, disabled: !projectData.isLoaded },
    { id: 'chat', label: 'AI 튜터', icon: MessageSquare, disabled: !projectData.isLoaded },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <div className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-center h-16 border-b border-gray-200">
          <h1 className="text-xl font-bold text-indigo-600 flex items-center gap-2">
            <BookOpen className="w-6 h-6" />
            요약해조
          </h1>
        </div>

        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                if (!item.disabled) {
                  setActivePage(item.id);
                  setIsMobileOpen(false);
                }
              }}
              disabled={item.disabled}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors
                ${activePage === item.id 
                  ? 'bg-indigo-50 text-indigo-700' 
                  : item.disabled 
                    ? 'text-gray-400 cursor-not-allowed' 
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
              {item.disabled && <span className="ml-auto text-xs bg-gray-100 px-2 py-0.5 rounded">필수</span>}
            </button>
          ))}
        </nav>

        {projectData.isLoaded && (
          <div className="absolute bottom-0 w-full p-4 border-t border-gray-200 bg-gray-50">
            <p className="text-xs text-gray-500 mb-1">현재 학습 중인 자료</p>
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-800 truncate">
              {projectData.type === 'youtube' && <Youtube className="w-4 h-4 text-red-500" />}
              {projectData.type === 'file' && <FileText className="w-4 h-4 text-blue-500" />}
              {projectData.type === 'text' && <Type className="w-4 h-4 text-gray-500" />}
              <span className="truncate">{projectData.fileName}</span>
            </div>
          </div>
        )}
      </div>
    </>
  );
};


/**
 * [페이지 컴포넌트 1: 업로드 페이지]
 * 사용자가 자료를 올리는 핵심 영역입니다.
 */
const UploadPage = ({ onUploadSuccess }) => {
  const { updateProjectData, resetProjectData } = useProject();
  const [activeTab, setActiveTab] = useState('file'); // file, youtube, text
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  
  // Input Refs
  const fileInputRef = useRef(null);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [rawText, setRawText] = useState('');

  // 탭 변경 시 데이터 초기화
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setUploadProgress(0);
  };

  // 파일 처리 시뮬레이션
  const processUpload = (type, name, content) => {
    setIsUploading(true);
    resetProjectData();

    // 실제 API 통신을 흉내내는 타이머 (Progress Bar 구현용)
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadProgress(progress);
      
      if (progress >= 100) {
        clearInterval(interval);
        
        // 전역 상태 업데이트 (이게 핵심입니다!)
        updateProjectData({
          isLoaded: true,
          type: type,
          fileName: name,
          content: content,
          uploadDate: new Date().toISOString(),
          // 실제로는 여기서 API 응답받은 요약본, 퀴즈 등을 같이 저장합니다.
          summary: "API에서 생성된 요약 내용이 들어갑니다...", 
        });

        setIsUploading(false);
        onUploadSuccess(); // 다음 페이지로 이동
      }
    }, 200); // 0.2초마다 10% 증가
  };

  // 1. 파일 업로드 핸들러
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      processUpload('file', file.name, file);
    }
  };

  // 2. 유튜브 링크 핸들러
  const handleYoutubeSubmit = () => {
    if (!youtubeUrl.includes('youtube.com') && !youtubeUrl.includes('youtu.be')) {
      alert('유효한 유튜브 링크를 입력해주세요.');
      return;
    }
    // 유튜브 영상 ID 추출 로직은 생략하고 예시로 처리
    processUpload('youtube', 'Youtube Lecture Video', youtubeUrl);
  };

  // 3. 텍스트 직접 입력 핸들러
  const handleTextSubmit = () => {
    if (rawText.length < 10) {
      alert('내용을 더 입력해주세요.');
      return;
    }
    const title = rawText.slice(0, 20) + '...';
    processUpload('text', title, rawText);
  };

  // 드래그 앤 드롭 UI 로직
  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      processUpload('file', file.name, file);
    }
  };

  return (
    <div className="max-w-3xl mx-auto pt-8 px-4">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">강의 자료를 올려주세요</h2>
        <p className="text-gray-600">
          PDF, PPT, 영상 링크, 혹은 텍스트를 올리면<br/>AI가 요약 노트와 퀴즈를 만들어 드립니다.
        </p>
      </div>

      {/* 업로드 타입 선택 탭 */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden mb-8">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => handleTabChange('file')}
            className={`flex-1 py-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'file' ? 'bg-indigo-50 text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <FileText className="w-4 h-4" /> 파일 업로드
          </button>
          <button
            onClick={() => handleTabChange('youtube')}
            className={`flex-1 py-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'youtube' ? 'bg-indigo-50 text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <Youtube className="w-4 h-4" /> 유튜브 링크
          </button>
          <button
            onClick={() => handleTabChange('text')}
            className={`flex-1 py-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'text' ? 'bg-indigo-50 text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <Type className="w-4 h-4" /> 텍스트 입력
          </button>
        </div>

        {/* 탭 컨텐츠 영역 */}
        <div className="p-8 min-h-[300px] flex flex-col justify-center">
          
          {/* 1. 파일 업로드 UI */}
          {activeTab === 'file' && (
            <div 
              className={`border-2 border-dashed rounded-xl p-10 text-center transition-all ${isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="w-16 h-16 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Upload className="w-8 h-8" />
              </div>
              <p className="text-gray-900 font-medium mb-2">파일을 이곳에 드래그하거나 클릭하세요</p>
              <p className="text-gray-500 text-sm mb-6">지원 형식: PDF, PPTX, MP4 (최대 50MB)</p>
              <input 
                type="file" 
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".pdf,.ppt,.pptx,.mp4,.mov" 
                className="hidden" 
              />
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
                disabled={isUploading}
              >
                파일 선택하기
              </button>
            </div>
          )}

          {/* 2. 유튜브 UI */}
          {activeTab === 'youtube' && (
            <div className="max-w-lg mx-auto w-full">
              <label className="block text-sm font-medium text-gray-700 mb-2">유튜브 영상 URL</label>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..." 
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
                <button 
                  onClick={handleYoutubeSubmit}
                  disabled={isUploading || !youtubeUrl}
                  className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors font-medium flex items-center gap-2"
                >
                  {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : '분석'}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">영상 길이에 따라 분석 시간이 소요될 수 있습니다.</p>
            </div>
          )}

          {/* 3. 텍스트 UI */}
          {activeTab === 'text' && (
            <div className="h-full flex flex-col">
              <textarea 
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="강의 내용이나 요약하고 싶은 텍스트를 직접 붙여넣으세요..."
                className="w-full h-48 border border-gray-300 rounded-lg p-4 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none mb-4"
              />
              <button 
                onClick={handleTextSubmit}
                disabled={isUploading || !rawText}
                className="self-end bg-gray-900 text-white px-8 py-3 rounded-lg hover:bg-gray-800 transition-colors font-medium flex items-center gap-2"
              >
                {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : '요약 노트 생성'}
                {!isUploading && <ArrowRight className="w-4 h-4" />}
              </button>
            </div>
          )}
        </div>

        {/* 로딩 프로그레스 바 (업로드 중일 때만 표시) */}
        {isUploading && (
          <div className="bg-gray-50 p-4 border-t border-gray-100">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>자료 분석 및 업로드 중...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300 ease-out" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


/**
 * [페이지 컴포넌트 2: 강의 노트 페이지 (결과 확인용)]
 * 업로드된 데이터가 잘 공유되었는지 확인하는 페이지입니다.
 */
const NotesPage = () => {
  const { projectData } = useProject();

  if (!projectData.isLoaded) return <div>데이터가 없습니다.</div>;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-start gap-3">
        <CheckCircle className="w-6 h-6 text-green-600 mt-0.5" />
        <div>
          <h3 className="font-bold text-green-800">업로드 성공! 데이터가 연동되었습니다.</h3>
          <p className="text-green-700 text-sm">
            업로드 페이지에서 입력한 데이터가 이 '노트 생성' 페이지까지 전달되었습니다.<br/>
            실제 프로젝트에서는 여기에 AI가 생성한 마크다운 형식이 렌더링 됩니다.
          </p>
        </div>
      </div>

      <div className="bg-white border shadow-sm rounded-xl p-8">
        <h1 className="text-3xl font-bold mb-2">{projectData.fileName}</h1>
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-8 pb-8 border-b">
          <span className="bg-gray-100 px-2 py-1 rounded uppercase font-semibold">{projectData.type}</span>
          <span>{new Date(projectData.uploadDate).toLocaleString()}</span>
        </div>

        <div className="prose max-w-none">
          <h3>AI 요약 노트</h3>
          <p className="text-gray-600 leading-relaxed">
            (여기에 백엔드 API에서 받아온 요약 내용이 표시됩니다.)<br/><br/>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
          </p>
          {/* 만약 텍스트 입력이었다면 원본 표시 */}
          {projectData.type === 'text' && (
             <div className="mt-8 bg-gray-50 p-4 rounded-lg">
                <h4 className="font-bold mb-2">원본 텍스트</h4>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{projectData.content}</p>
             </div>
          )}
        </div>
      </div>
    </div>
  );
};


/**
 * [메인 App 컴포넌트]
 * 라우팅 및 레이아웃 구조
 */
const AppContent = () => {
  const [activePage, setActivePage] = useState('upload'); // 'upload', 'notes', 'chat'
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  
  // 업로드 완료 시 자동으로 노트 페이지로 이동시키는 함수
  const handleUploadSuccess = () => {
    // 잠시 후 페이지 이동 (UX 효과)
    setTimeout(() => {
      setActivePage('notes');
    }, 500);
  };

  return (
    <div className="flex h-screen bg-gray-50 font-sans">
      {/* Sidebar */}
      <Sidebar 
        activePage={activePage} 
        setActivePage={setActivePage} 
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="lg:hidden bg-white border-b border-gray-200 p-4 flex items-center gap-4">
          <button onClick={() => setIsMobileOpen(true)} className="text-gray-600">
            <Menu className="w-6 h-6" />
          </button>
          <span className="font-bold text-lg">요약해조</span>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {activePage === 'upload' && <UploadPage onUploadSuccess={handleUploadSuccess} />}
          {activePage === 'notes' && <NotesPage />}
          {activePage === 'chat' && (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>챗봇 페이지 예시입니다.<br/>업로드한 '{useProject().projectData.fileName}' 내용을 바탕으로 대화합니다.</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

// 최상위 컴포넌트에서 Provider 감싸기
export default function App() {
  return (
    <ProjectProvider>
      <AppContent />
    </ProjectProvider>
  );
}