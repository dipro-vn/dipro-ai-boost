export interface ExplorerFolderTarget {
  path: string;
  name: string;
}

/** Mục được chuột phải — file hay folder đều được, nên mọi chỗ dựng menu
 * phải biết nó là loại nào để hiện đúng thao tác. */
export interface ExplorerEntryTarget extends ExplorerFolderTarget {
  isDir: boolean;
}

export interface ExplorerContextTarget extends ExplorerEntryTarget {
  x: number;
  y: number;
}

export type ExplorerCreateKind = "file" | "folder";

/** Thuộc tính đánh dấu một hàng folder trong cây, để lúc thả file còn hit-test
 * ngược từ toạ độ con trỏ ra folder đích. Sự kiện kéo-thả của Tauri chỉ cho
 * toạ độ, không cho biết đang ở trên phần tử DOM nào. */
export const EXPLORER_DIR_PATH_ATTR = "data-explorer-dir-path";
