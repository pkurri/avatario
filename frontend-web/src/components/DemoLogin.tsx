"use client";

import { FormEvent, useState } from "react";
import { LogIn, LogOut, UserRound } from "lucide-react";
import { useDemoUser } from "@/hooks/useDemoUser";
import { apiUrl } from "@/lib/config";

export function DemoLogin() {
  const { user, isLoggedIn, isStorageReady, loginDemoUser, logoutDemoUser } = useDemoUser();
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const demoUser = {
      name: name.trim() || user.name,
      email: email.trim() || user.email,
    };

    try {
      const response = await fetch(apiUrl("/demo/login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(demoUser),
      });
      const data = await response.json();
      window.localStorage.setItem("avatario.demoSessionId", data.session_id);
      loginDemoUser(data.user || demoUser);
    } catch {
      loginDemoUser(demoUser);
    }
  };

  if (!isStorageReady) {
    return null;
  }

  if (isLoggedIn) {
    return (
      <div className="fixed top-20 right-4 z-50 flex max-w-[calc(100vw-2rem)] items-center gap-3 rounded-lg border border-white/10 bg-[#0f1420]/95 px-3 py-2 text-white shadow-xl backdrop-blur">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-500/15 text-blue-300">
          <UserRound className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{user.name}</p>
          <p className="truncate text-xs text-neutral-400">Demo session active</p>
        </div>
        <button
          type="button"
          onClick={logoutDemoUser}
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-neutral-400 transition hover:bg-white/10 hover:text-white"
          aria-label="Sign out demo user"
          title="Sign out"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="fixed top-20 right-4 z-50 w-[min(22rem,calc(100vw-2rem))] rounded-lg border border-white/10 bg-[#0f1420]/95 p-3 text-white shadow-xl backdrop-blur"
    >
      <div className="mb-3 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-500/15 text-blue-300">
          <LogIn className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold">Demo login</p>
          <p className="text-xs text-neutral-400">Use a local test session.</p>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="min-w-0 rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none transition placeholder:text-neutral-500 focus:border-blue-400"
          placeholder="Name"
        />
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="min-w-0 rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none transition placeholder:text-neutral-500 focus:border-blue-400"
          placeholder="Email"
          type="email"
        />
      </div>
      <button
        type="submit"
        className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-500"
      >
        <LogIn className="h-4 w-4" />
        Start session
      </button>
    </form>
  );
}
