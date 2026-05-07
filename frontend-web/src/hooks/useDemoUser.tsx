"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export interface DemoUser {
  id: string;
  name: string;
  email: string;
  role: string;
  preferences: {
    theme: "dark" | "light";
    language: string;
    notifications: boolean;
  };
  stats: {
    callsHandled: number;
    meetingsScheduled: number;
    tasksCompleted: number;
  };
}

const defaultDemoUser: DemoUser = {
  id: "demo-001",
  name: "Alex Sharma",
  email: "alex.sharma@example.com",
  role: "Product Manager",
  preferences: {
    theme: "dark",
    language: "English",
    notifications: true,
  },
  stats: {
    callsHandled: 47,
    meetingsScheduled: 12,
    tasksCompleted: 28,
  },
};

interface DemoUserContextType {
  user: DemoUser;
  isLoggedIn: boolean;
  isStorageReady: boolean;
  updateUser: (updates: Partial<DemoUser>) => void;
  updateStats: (key: keyof DemoUser["stats"], increment?: number) => void;
  loginDemoUser: (updates?: Partial<DemoUser>) => void;
  logoutDemoUser: () => void;
  isOnboarding: boolean;
  completeOnboarding: () => void;
}

const DemoUserContext = createContext<DemoUserContextType | undefined>(undefined);
const DEMO_USER_STORAGE_KEY = "avatario.demoUser";
const DEMO_LOGIN_STORAGE_KEY = "avatario.demoLoggedIn";

export function DemoUserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<DemoUser>(defaultDemoUser);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isOnboarding, setIsOnboarding] = useState(false);
  const [hasLoadedStorage, setHasLoadedStorage] = useState(false);

  useEffect(() => {
    const loadStorage = window.setTimeout(() => {
      const savedUser = window.localStorage.getItem(DEMO_USER_STORAGE_KEY);
      if (savedUser) {
        try {
          setUser({ ...defaultDemoUser, ...JSON.parse(savedUser) });
        } catch {
          setUser(defaultDemoUser);
        }
      }
      setIsLoggedIn(window.localStorage.getItem(DEMO_LOGIN_STORAGE_KEY) === "true");
      setHasLoadedStorage(true);
    }, 0);

    return () => window.clearTimeout(loadStorage);
  }, []);

  useEffect(() => {
    if (!hasLoadedStorage) return;
    window.localStorage.setItem(DEMO_USER_STORAGE_KEY, JSON.stringify(user));
  }, [hasLoadedStorage, user]);

  useEffect(() => {
    if (!hasLoadedStorage) return;
    window.localStorage.setItem(DEMO_LOGIN_STORAGE_KEY, String(isLoggedIn));
  }, [hasLoadedStorage, isLoggedIn]);

  const updateUser = (updates: Partial<DemoUser>) => {
    setUser((prev) => ({ ...prev, ...updates }));
  };

  const updateStats = (key: keyof DemoUser["stats"], increment = 1) => {
    setUser((prev) => ({
      ...prev,
      stats: {
        ...prev.stats,
        [key]: prev.stats[key] + increment,
      },
    }));
  };

  const completeOnboarding = () => setIsOnboarding(false);
  const loginDemoUser = (updates: Partial<DemoUser> = {}) => {
    setUser((prev) => ({ ...prev, ...updates }));
    setIsLoggedIn(true);
    setIsOnboarding(false);
  };
  const logoutDemoUser = () => {
    setIsLoggedIn(false);
    setIsOnboarding(false);
  };

  return (
    <DemoUserContext.Provider
      value={{
        user,
        isLoggedIn,
        isStorageReady: hasLoadedStorage,
        updateUser,
        updateStats,
        loginDemoUser,
        logoutDemoUser,
        isOnboarding,
        completeOnboarding,
      }}
    >
      {children}
    </DemoUserContext.Provider>
  );
}

export function useDemoUser() {
  const context = useContext(DemoUserContext);
  if (!context) {
    throw new Error("useDemoUser must be used within DemoUserProvider");
  }
  return context;
}
