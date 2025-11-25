/**
 * Explorer Page - GitHub-style file tree + code viewer + file summary
 * Protected: Requires sessionId and repoId
 */

import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { useGetRepository } from "@/hooks/query/repository";
import { useTaskPolling } from "@/hooks/query/task";
import ProgressUI from "@/components/ProgressUI";
import { FileTree } from "@/components/file-tree";

export default function Explorer() {
  const { repoId } = useParams<{ repoId: string }>();

  // State for selected file in the tree
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);

  // Step 1: Fetch repository status (runs on mount and reload)
  const { repository, isLoading, isError, error, isProcessing, isCompleted, isFailed, refetch } =
    useGetRepository(repoId);

  // Step 2: Start polling task if repository is processing
  const { task } = useTaskPolling({
    taskId: repository?.task_id,
    enabled: isProcessing, // Only poll when status is "processing"
  });

  // Step 3: Refetch repository when task completes
  useEffect(() => {
    if (task?.status === "completed" || task?.status === "failed") {
      console.log("🔄 Task completed/failed - refetching repository status");
      refetch();
    }
  }, [task?.status, refetch]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--bg-primary)]">
        <div className="text-center space-y-4">
          <div className="animate-spin h-12 w-12 border-4 border-purple-500 border-t-transparent rounded-full mx-auto"></div>
          <p className="text-[var(--text-secondary)]">Loading repository...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--bg-primary)]">
        <div className="text-center space-y-4 max-w-md">
          <div className="text-red-500 text-5xl">⚠️</div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Failed to load repository
          </h2>
          <p className="text-[var(--text-secondary)]">
            {error instanceof Error ? error.message : "Unknown error occurred"}
          </p>
        </div>
      </div>
    );
  }

  // Failed processing state
  if (isFailed) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--bg-primary)]">
        <div className="text-center space-y-4 max-w-md">
          <div className="text-red-500 text-5xl">❌</div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Processing Failed
          </h2>
          <p className="text-[var(--text-secondary)]">
            {repository?.error_message || "Failed to process repository"}
          </p>
        </div>
      </div>
    );
  }

  // Processing state - Show progress UI
  if (isProcessing) {
    return <ProgressUI task={task} repositoryName={repository?.full_name} />;
  }

  // Completed state - Show file explorer
  if (isCompleted) {
    // Debug: Check what file_tree looks like
    
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
        {/* Layout: File Tree (25%) | Code Viewer + Summary (75%) */}
        <div className="flex h-screen">
          {/* Left Sidebar - File Tree */}
          <div className="w-1/4 border-r border-[var(--border-color)] bg-[var(--bg-secondary)] overflow-auto">
            {/* Header */}
            <div className="p-4 border-b border-[var(--border-color)]">
              <h2 className="text-lg font-semibold">{repository?.full_name}</h2>
              <p className="text-sm text-[var(--text-secondary)]">
                {repository?.file_count} files
              </p>
            </div>

            {/* File Tree */}
            <div className="py-2">
              <FileTree
                tree={repository?.file_tree}
                onFileSelect={setSelectedFilePath}
                selectedPath={selectedFilePath}
              />
            </div>
          </div>

          {/* Right Panel - Code + Summary */}
          <div className="flex-1 flex flex-col">
            {/* Code Viewer */}
            <div className="flex-1 p-6 overflow-auto">
              {selectedFilePath ? (
                <>
                  <h2 className="text-xl font-semibold mb-4 font-mono">
                    {selectedFilePath}
                  </h2>
                  <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-4">
                    <p className="text-[var(--text-secondary)]">
                      Code viewer coming soon...
                    </p>
                    <p className="text-sm text-[var(--text-muted)] mt-2">
                      Selected: {selectedFilePath}
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <h2 className="text-xl font-semibold mb-4">Code Preview</h2>
                  <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-4">
                    <p className="text-[var(--text-secondary)]">
                      Select a file from the tree to view its contents with syntax highlighting
                    </p>
                  </div>
                </>
              )}
            </div>

            {/* File Summary Section */}
            <div className="h-64 border-t border-[var(--border-color)] bg-[var(--bg-secondary)] p-6 overflow-auto">
              <h3 className="text-lg font-semibold mb-3">AI Summary</h3>
              {selectedFilePath ? (
                <p className="text-sm text-[var(--text-secondary)]">
                  Loading summary for {selectedFilePath}...
                </p>
              ) : (
                <p className="text-sm text-[var(--text-secondary)]">
                  AI-generated file summary will appear here when you select a file
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Fallback (shouldn't reach here)
  return null;
}
