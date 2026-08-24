import { Boxes } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { EcosystemRepo } from "@/lib/tauri-client";

export function EcosystemRepoTable({ repos }: { repos: EcosystemRepo[] }) {
  if (repos.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-6 text-center">
        <Boxes className="size-8 text-muted-foreground/40" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">
          Không có repo nào trong bảng Ecosystem của AGENTS.md.
        </p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Repo</TableHead>
          <TableHead>Đường dẫn</TableHead>
          <TableHead>Vai trò</TableHead>
          <TableHead>Stack</TableHead>
          <TableHead>Trạng thái</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {repos.map((repo) => (
          <TableRow key={`${repo.name}-${repo.declaredPath}`}>
            <TableCell className="font-medium">{repo.name}</TableCell>
            <TableCell className="font-mono text-xs text-muted-foreground">
              {repo.declaredPath}
            </TableCell>
            <TableCell>{repo.role}</TableCell>
            <TableCell>{repo.stack}</TableCell>
            <TableCell>
              {repo.cloned ? (
                <Badge variant="secondary">đã clone</Badge>
              ) : (
                <Badge variant="destructive">chưa clone</Badge>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
