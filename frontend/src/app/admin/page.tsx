"use client";

import { AdminProvider } from "./_context/AdminContext";
import { AdminShell } from "./_components/AdminShell";

export default function AdminPage() {
  return (
    <AdminProvider>
      <AdminShell />
    </AdminProvider>
  );
}
