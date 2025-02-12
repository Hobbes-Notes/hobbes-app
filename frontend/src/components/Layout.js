import React from 'react';
import { ScrollArea } from "../components/ui/scroll-area";
import { Separator } from "../components/ui/separator";

export function Layout({ children, sidebar }) {
  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <div className="w-80 border-r bg-gray-50/40 pb-12">
        <div className="space-y-4 py-4">
          <div className="px-3 py-2">
            <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">
              Projects
            </h2>
            <ScrollArea className="h-[calc(100vh-6rem)]">
              {sidebar}
            </ScrollArea>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1">
        <div className="h-full px-8 py-6">
          {children}
        </div>
      </div>
    </div>
  );
} 