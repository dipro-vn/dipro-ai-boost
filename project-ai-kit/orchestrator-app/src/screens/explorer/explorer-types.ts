export interface ExplorerFolderTarget {
  path: string;
  name: string;
}

export interface ExplorerContextTarget extends ExplorerFolderTarget {
  x: number;
  y: number;
}

export type ExplorerCreateKind = "file" | "folder";
