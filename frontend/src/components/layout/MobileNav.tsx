"use client";

import { X } from "lucide-react";
import Sidebar from "./Sidebar";
import type { NavItem } from "@/config/navigation";

interface MobileNavProps {
  navigation: NavItem[];
  open: boolean;
  setOpen: (open: boolean) => void;
}

export default function MobileNav({ navigation, open, setOpen }: MobileNavProps) {
  if (!open) return null;

  return (
    <div className="relative z-50 lg:hidden">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/80 transition-opacity" 
        onClick={() => setOpen(false)}
        aria-hidden="true"
      />

      <div className="fixed inset-0 flex">
        <div className="relative mr-16 flex w-full max-w-xs flex-1">
          {/* Close button */}
          <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
            <button
              type="button"
              className="-m-2.5 p-2.5 text-white"
              onClick={() => setOpen(false)}
            >
              <span className="sr-only">Close sidebar</span>
              <X className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>

          {/* Sidebar component inside mobile drawer */}
          <Sidebar navigation={navigation} onItemClick={() => setOpen(false)} />
        </div>
      </div>
    </div>
  );
}
