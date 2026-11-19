"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { api, type Organization } from "@/lib/api";

interface OrgContextValue {
  organizations: Organization[];
  organizationId: string | null;
  setOrganizationId: (id: string) => void;
  loading: boolean;
  error: string | null;
  seedDemo: () => Promise<void>;
  seeding: boolean;
}

const OrgContext = createContext<OrgContextValue | null>(null);

const STORAGE_KEY = "mi.organizationId";

export function OrgProvider({ children }: { children: React.ReactNode }) {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organizationId, setOrganizationIdState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const orgs = await api.listOrganizations();
      setOrganizations(orgs);
      const stored = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
      const match = orgs.find((o) => o.id === stored);
      setOrganizationIdState(match ? match.id : orgs[0]?.id ?? null);
    } catch {
      setError("לא ניתן להתחבר ל-API של השרת. בדקו שהבקאנד פועל.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const setOrganizationId = useCallback((id: string) => {
    setOrganizationIdState(id);
    if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, id);
  }, []);

  const seedDemo = useCallback(async () => {
    setSeeding(true);
    try {
      const result = await api.seedDemo();
      await load();
      setOrganizationId(result.organization_id);
    } finally {
      setSeeding(false);
    }
  }, [load, setOrganizationId]);

  return (
    <OrgContext.Provider
      value={{ organizations, organizationId, setOrganizationId, loading, error, seedDemo, seeding }}
    >
      {children}
    </OrgContext.Provider>
  );
}

export function useOrg() {
  const ctx = useContext(OrgContext);
  if (!ctx) throw new Error("useOrg must be used within OrgProvider");
  return ctx;
}
