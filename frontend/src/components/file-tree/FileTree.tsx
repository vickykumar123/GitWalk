/**
 * FileTree Component - GitHub-style file tree with expandable folders
 *
 * KEY CONCEPTS:
 * 1. Recursive Rendering - TreeNode calls itself for nested children
 * 2. State Management - Track which folders are expanded
 * 3. Sorting - Folders first, then files, alphabetically
 */

import { useState, useEffect } from "react";
import type { FileTreeNode as FileTreeNodeType } from "@/types";

// ==================== Icons ====================

// Simple SVG icons (you can replace with lucide-react later)
const FolderIcon = ({ isOpen }: { isOpen: boolean }) => (
  <svg
    className={`w-4 h-4 ${isOpen ? "text-yellow-400" : "text-yellow-500"}`}
    fill="currentColor"
    viewBox="0 0 20 20"
  >
    {isOpen ? (
      // Open folder
      <path
        fillRule="evenodd"
        d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1H3a1 1 0 00-1 1v5a2 2 0 002 2h10a2 2 0 002-2V8a2 2 0 00-2-2h-1.586l-2-2H4z"
        clipRule="evenodd"
      />
    ) : (
      // Closed folder
      <path d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
    )}
  </svg>
);

const FileIcon = ({ language }: { language?: string }) => {
  // Color based on language
  const getColor = () => {
    switch (language?.toLowerCase()) {
      case "python":
        return "text-blue-400";
      case "javascript":
        return "text-yellow-400";
      case "typescript":
        return "text-blue-500";
      case "rust":
        return "text-orange-500";
      case "go":
        return "text-cyan-400";
      case "java":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  return (
    <svg className={`w-4 h-4 ${getColor()}`} fill="currentColor" viewBox="0 0 20 20">
      <path
        fillRule="evenodd"
        d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
        clipRule="evenodd"
      />
    </svg>
  );
};

const ChevronIcon = ({ isOpen }: { isOpen: boolean }) => (
  <svg
    className={`w-3 h-3 text-gray-500 transition-transform ${isOpen ? "rotate-90" : ""}`}
    fill="currentColor"
    viewBox="0 0 20 20"
  >
    <path
      fillRule="evenodd"
      d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
      clipRule="evenodd"
    />
  </svg>
);

// ==================== Tree Node Component ====================

interface TreeNodeProps {
  name: string;
  node: FileTreeNodeType;
  depth: number;
  currentPath: string; // Full path to this node (built during traversal)
  onFileSelect: (path: string) => void;
  selectedPath: string | null;
  disabled?: boolean; // When true, folders can expand but files can't be clicked
  expandToPath?: string | null; // Path to auto-expand to (from graph click)
}

function TreeNode({ name, node, depth, currentPath, onFileSelect, selectedPath, disabled, expandToPath }: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false); // All collapsed initially
  const isFolder = node.type === "folder";
  // Use node.path for files (from backend) or currentPath for folders (built during traversal)
  const nodePath = node.path || currentPath;
  const isSelected = nodePath === selectedPath;
  const isFileDisabled = !isFolder && disabled;

  // Auto-expand if this folder is in the path to expandToPath
  useEffect(() => {
    if (isFolder && expandToPath && currentPath) {
      // Check if expandToPath starts with this folder's path
      // e.g., if currentPath is "src" and expandToPath is "src/components/Button.tsx"
      if (expandToPath.startsWith(currentPath + "/")) {
        setIsExpanded(true);
      }
    }
  }, [expandToPath, isFolder, currentPath]);

  // Handle click
  const handleClick = () => {
    if (isFolder) {
      // Folders can always expand/collapse
      setIsExpanded(!isExpanded);
    } else if (nodePath && !disabled) {
      // Files only clickable when not disabled
      onFileSelect(nodePath);
    }
  };

  // Sort children: folders first, then files, alphabetically
  const sortedChildren = node.children
    ? Object.entries(node.children).sort(([aName, aNode], [bName, bNode]) => {
        // Folders before files
        if (aNode.type !== bNode.type) {
          return aNode.type === "folder" ? -1 : 1;
        }
        // Alphabetical within same type
        return aName.localeCompare(bName);
      })
    : [];

  return (
    <div>
      {/* Node row */}
      <div
        onClick={handleClick}
        className={`
          flex items-center gap-1 py-1 px-2 rounded
          ${isFileDisabled
            ? "opacity-50 cursor-not-allowed"
            : "cursor-pointer hover:bg-[var(--bg-hover)]"
          }
          ${isSelected ? "bg-purple-500/20 text-purple-300 font-medium" : ""}
        `}
        style={{ paddingLeft: `${depth * 16 + 4}px` }}
      >
        {/* Chevron for folders */}
        {isFolder ? (
          <ChevronIcon isOpen={isExpanded} />
        ) : (
          <span className="w-3" /> // Spacer for alignment
        )}

        {/* Icon */}
        {isFolder ? <FolderIcon isOpen={isExpanded} /> : <FileIcon language={node.language} />}

        {/* Name */}
        <span className="text-sm truncate">{name}</span>
      </div>

      {/* Children (recursive!) */}
      {isFolder && isExpanded && sortedChildren.length > 0 && (
        <div>
          {sortedChildren.map(([childName, childNode]) => (
            <TreeNode
              key={childName}
              name={childName}
              node={childNode}
              depth={depth + 1}
              currentPath={currentPath ? `${currentPath}/${childName}` : childName}
              onFileSelect={onFileSelect}
              selectedPath={selectedPath}
              disabled={disabled}
              expandToPath={expandToPath}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ==================== Main FileTree Component ====================

interface FileTreeProps {
  tree: FileTreeNodeType | null | undefined;
  onFileSelect: (path: string) => void;
  selectedPath: string | null;
  disabled?: boolean; // When true, folders can expand but files can't be clicked
  expandToPath?: string | null; // Path to auto-expand folders to (from graph click)
}

export default function FileTree({ tree, onFileSelect, selectedPath, disabled, expandToPath }: FileTreeProps) {
  // Handle empty/null tree
  if (!tree || Object.keys(tree).length === 0) {
    return (
      <div className="text-sm text-[var(--text-secondary)] p-4">
        No files to display
      </div>
    );
  }

  // Backend returns tree as direct children (not wrapped in root node)
  // So tree = { "src": {...}, "README.md": {...} }
  // NOT tree = { type: "folder", children: {...} }
  const rootChildren = tree.children
    ? tree.children  // If wrapped in root node
    : tree as unknown as Record<string, FileTreeNodeType>;  // Direct children

  // Sort root children
  const sortedRootChildren = Object.entries(rootChildren).sort(
    ([aName, aNode], [bName, bNode]) => {
      if (aNode.type !== bNode.type) {
        return aNode.type === "folder" ? -1 : 1;
      }
      return aName.localeCompare(bName);
    }
  );

  return (
    <div className="text-[var(--text-primary)]">
      {sortedRootChildren.map(([name, node]) => (
        <TreeNode
          key={name}
          name={name}
          node={node}
          depth={0}
          currentPath={name}
          onFileSelect={onFileSelect}
          selectedPath={selectedPath}
          disabled={disabled}
          expandToPath={expandToPath}
        />
      ))}
    </div>
  );
}
