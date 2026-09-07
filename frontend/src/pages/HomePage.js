import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Truck, ShieldCheck, Clock3, PackageSearch, ArrowRight, SearchX } from "lucide-react";
import { api, errorMessage } from "@/lib/api";
import { ProductCard } from "@/components/ProductCard";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { cn } from "@/lib/utils";

const HERO_IMG =
  "https://images.unsplash.com/photo-1570086625846-f33f679eb4f5?crop=entropy&cs=srgb&fm=jpg&q=80&w=1200";

export default function HomePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const q = new URLSearchParams(location.search).get("q") || "";
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeCat, setActiveCat] = useState("");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");
    api
      .get("/home", { params: q ? { q } : {} })
      .then((r) => alive && setData(r.data))
      .catch((e) => alive && setError(errorMessage(e, "Gagal memuat katalog produk")))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [q]);

  const categories = useMemo(() => (data?.categories || []).filter((c) => c.products.length > 0), [data]);

  const scrollTo = (slug) => {
    setActiveCat(slug);
    const el = document.getElementById(`kategori-${slug}`);
    if (el) {
      const y = el.getBoundingClientRect().top + window.scrollY - 128;
      window.scrollTo({ top: y, behavior: "smooth" });
    }
  };

  return (
    <div className="pb-10">
      {/* Hero */}
      {!q && (
        <section className="hero-gradient noise-bg border-b">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:px-6 sm:py-14 lg:grid-cols-[1.2fr_1fr] lg:items-center">
            <div className="animate-fade-up">
              <span className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
                <ShieldCheck className="h-3.5 w-3.5 text-primary" /> Supplier resmi bahan baku untuk Dapur MBG
              </span>
              <h1 className="mt-4 font-display text-3xl font-semibold leading-tight tracking-tight sm:text-4xl lg:text-5xl">
                Pasokan bahan baku segar, harga B2B transparan.
              </h1>
              <p className="mt-4 max-w-xl text-base text-muted-foreground sm:text-lg">
                Pesan beras, protein, sayur, buah, dan bumbu dalam jumlah besar. Checkout cepat tanpa registrasi, cukup nama lengkap dan nomor WA.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Button size="lg" className="gap-2 active:scale-[0.98]" onClick={() => categories[0] && scrollTo(categories[0].slug)} data-testid="hero-browse-button">
                  Lihat Katalog <ArrowRight className="h-4 w-4" />
                </Button>
                <Button size="lg" variant="secondary" onClick={() => navigate("/pesanan")}>
                  Cek Riwayat Pesanan
                </Button>
              </div>
              <dl className="mt-8 grid grid-cols-3 gap-4 text-sm">
                {[
                  { icon: Truck, t: "Kirim Terjadwal", d: "Pagi sebelum masak" },
                  { icon: Clock3, t: "Auto-verifikasi", d: "Transfer & e-wallet" },
                  { icon: PackageSearch, t: "Min. Order Jelas", d: "Per satuan produk" },
                ].map(({ icon: I, t, d }) => (
                  <div key={t} className="rounded-xl border bg-card p-3">
                    <I className="h-4 w-4 text-primary" />
                    <dt className="mt-2 font-semibold leading-tight">{t}</dt>
                    <dd className="text-xs text-muted-foreground">{d}</dd>
                  </div>
                ))}
              </dl>
            </div>
            <div className="hidden overflow-hidden rounded-2xl border bg-card shadow-sm lg:block">
              <img src={HERO_IMG} alt="Gudang bahan baku segar" className="h-[360px] w-full object-cover" />
            </div>
          </div>
        </section>
      )}

      {/* Category chips */}
      <div className="sticky top-16 z-30 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          {loading ? (
            <div className="flex gap-2 py-3">
              {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-8 w-28 rounded-full" />)}
            </div>
          ) : (
            <div className="no-scrollbar flex gap-2 overflow-x-auto py-3" data-testid="category-chips">
              {categories.map((c) => (
                <button
                  key={c.id}
                  data-testid="category-chip"
                  onClick={() => scrollTo(c.slug)}
                  className={cn(
                    "shrink-0 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
                    activeCat === c.slug ? "border-primary bg-accent text-accent-foreground" : "bg-secondary text-secondary-foreground hover:bg-muted"
                  )}
                >
                  {c.name} <span className="ml-1 text-xs text-muted-foreground">{c.products.length}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        {q && (
          <div className="flex flex-wrap items-center justify-between gap-2 pt-6">
            <p className="text-sm text-muted-foreground">
              Hasil pencarian untuk <span className="font-semibold text-foreground">"{q}"</span> &middot; {data?.total_products ?? 0} produk
            </p>
            <Button variant="ghost" size="sm" onClick={() => navigate("/")} data-testid="clear-search-button">Hapus pencarian</Button>
          </div>
        )}

        {error && (
          <div className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800" data-testid="home-error">
            {error}
          </div>
        )}

        {loading ? (
          <div className="space-y-10 pt-8">
            {[...Array(2)].map((_, s) => (
              <div key={s}>
                <Skeleton className="mb-4 h-7 w-56" />
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 sm:gap-4">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="overflow-hidden rounded-xl border bg-card">
                      <Skeleton className="aspect-square w-full rounded-none" />
                      <div className="space-y-2 p-4">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                        <Skeleton className="h-9 w-full" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : categories.length === 0 && !error ? (
          <div className="pt-8">
            <EmptyState
              icon={SearchX}
              title={q ? "Produk tidak ditemukan" : "Belum ada produk"}
              description={q ? "Coba kata kunci lain, misalnya 'beras' atau 'ayam'." : "Admin belum menambahkan produk ke katalog."}
              actionLabel={q ? "Lihat semua produk" : undefined}
              onAction={() => navigate("/")}
              testId="home-empty-state"
            />
          </div>
        ) : (
          <div className="space-y-12 pt-8">
            {categories.map((c) => (
              <section key={c.id} id={`kategori-${c.slug}`} data-testid="category-section" className="scroll-mt-32">
                <div className="mb-4 flex items-end justify-between gap-4">
                  <div>
                    <h2 className="font-display text-xl font-semibold sm:text-2xl" data-testid="category-title">{c.name}</h2>
                    {c.description && <p className="mt-0.5 text-sm text-muted-foreground">{c.description}</p>}
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground">{c.products.length} produk</span>
                </div>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4" data-testid="product-grid">
                  {c.products.map((p) => (
                    <ProductCard key={p.id} product={p} />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
