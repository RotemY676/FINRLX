"use client";

import { AdminProvider } from "./_context/AdminContext";
import { AdminShell } from "./_components/AdminShell";
import { ToastProvider } from "./_components/ToastProvider";
import { ActivityProvider } from "./_components/ActivityFeed";

export default function AdminPage() {
  return (
    <AdminProvider>
      <ToastProvider>
        <ActivityProvider>
          <AdminShell />
        </ActivityProvider>
      </ToastProvider>
    </AdminProvider>
  );
}
