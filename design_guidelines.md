{
  "brand_attributes": [
    "Bersih, profesional, dan terpercaya (B2B procurement)",
    "Rapi & data-dense tanpa terasa sesak (mobile-first untuk dapur/field)",
    "Fresh-food cues (sage/teal) + enterprise grounding (navy/charcoal)",
    "Transparan: harga/unit, minimum order, status pembayaran/pesanan jelas"
  ],
  "design_personality": {
    "style_fusion": [
      "Swiss-style grid + whitespace (keterbacaan & hierarki)",
      "Bento cards untuk ringkasan (keranjang/checkout/admin KPI)",
      "Soft-industrial surfaces (warm gray) + aksen sage (fresh supply)",
      "Micro-interactions halus (hover lift, press scale, skeleton loading)"
    ],
    "do_not": [
      "Jangan layout serba center.",
      "Jangan background transparan.",
      "Jangan gradient gelap/saturated (lihat aturan gradient).",
      "Jangan pakai emoji sebagai ikon; gunakan lucide-react.",
      "Jangan pakai transition: all."
    ]
  },
  "typography": {
    "google_fonts": {
      "display": {
        "family": "Space Grotesk",
        "weights": [500, 600, 700],
        "usage": "Heading, angka KPI, harga total"
      },
      "body": {
        "family": "Manrope",
        "weights": [400, 500, 600],
        "usage": "Body, label form, tabel admin"
      }
    },
    "tailwind_font_tokens": {
      "font-sans": "Manrope, ui-sans-serif, system-ui",
      "font-display": "Space Grotesk, ui-sans-serif, system-ui"
    },
    "type_scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-display font-semibold tracking-tight",
      "h2": "text-base md:text-lg text-muted-foreground",
      "section_title": "text-xl sm:text-2xl font-display font-semibold",
      "card_title": "text-base font-semibold",
      "body": "text-sm sm:text-base",
      "small": "text-xs sm:text-sm text-muted-foreground"
    },
    "number_formatting": {
      "currency": "Rupiah: gunakan Intl.NumberFormat('id-ID') dan prefix 'Rp' (contoh: Rp 12.500)",
      "qty": "Tampilkan satuan (kg/liter/karton) dan MOQ (min. 5 kg) dekat stepper"
    }
  },
  "color_system": {
    "notes": [
      "Gunakan HSL tokens di index.css (:root) agar konsisten dengan shadcn.",
      "Tema utama: light (clean). Dark mode opsional untuk admin nanti, tapi tahap 1 fokus light."
    ],
    "tokens_hsl": {
      "background": "36 33% 98%",
      "foreground": "222 22% 12%",
      "card": "0 0% 100%",
      "card-foreground": "222 22% 12%",
      "popover": "0 0% 100%",
      "popover-foreground": "222 22% 12%",
      "primary": "164 42% 28%",
      "primary-foreground": "0 0% 98%",
      "secondary": "36 20% 94%",
      "secondary-foreground": "222 22% 14%",
      "muted": "36 18% 95%",
      "muted-foreground": "215 14% 42%",
      "accent": "164 35% 92%",
      "accent-foreground": "164 42% 18%",
      "border": "30 12% 88%",
      "input": "30 12% 88%",
      "ring": "164 42% 28%",
      "destructive": "0 72% 52%",
      "destructive-foreground": "0 0% 98%",
      "radius": "0.75rem",
      "chart-1": "164 42% 28%",
      "chart-2": "205 55% 38%",
      "chart-3": "28 78% 55%",
      "chart-4": "43 74% 56%",
      "chart-5": "222 22% 22%"
    },
    "semantic_status_colors": {
      "payment": {
        "pending": {"bg": "bg-amber-50", "text": "text-amber-800", "border": "border-amber-200"},
        "paid": {"bg": "bg-emerald-50", "text": "text-emerald-800", "border": "border-emerald-200"},
        "failed": {"bg": "bg-rose-50", "text": "text-rose-800", "border": "border-rose-200"},
        "expired": {"bg": "bg-zinc-50", "text": "text-zinc-700", "border": "border-zinc-200"},
        "cod": {"bg": "bg-sky-50", "text": "text-sky-800", "border": "border-sky-200"}
      },
      "order": {
        "baru": {"bg": "bg-slate-50", "text": "text-slate-800", "border": "border-slate-200"},
        "diproses": {"bg": "bg-amber-50", "text": "text-amber-800", "border": "border-amber-200"},
        "dikirim": {"bg": "bg-sky-50", "text": "text-sky-800", "border": "border-sky-200"},
        "selesai": {"bg": "bg-emerald-50", "text": "text-emerald-800", "border": "border-emerald-200"},
        "dibatalkan": {"bg": "bg-rose-50", "text": "text-rose-800", "border": "border-rose-200"}
      }
    },
    "gradient_usage": {
      "allowed": [
        "Hero background strip saja (maks 20% viewport)",
        "Decorative overlay di header (blurred blob kecil)",
        "Jangan untuk area baca panjang (tabel, form, deskripsi)"
      ],
      "safe_gradients_examples": [
        "bg-[radial-gradient(60%_60%_at_20%_10%,hsl(164_35%_92%)_0%,transparent_60%),radial-gradient(50%_50%_at_80%_0%,hsl(43_74%_92%)_0%,transparent_55%)]",
        "bg-[linear-gradient(135deg,hsl(36_33%_98%)_0%,hsl(164_35%_96%)_55%,hsl(36_33%_98%)_100%)]"
      ]
    }
  },
  "layout_and_grid": {
    "container": "max-w-6xl mx-auto px-4 sm:px-6",
    "page_spacing": "py-6 sm:py-10",
    "catalog_grid": "grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4",
    "admin_grid": "grid grid-cols-1 lg:grid-cols-12 gap-4",
    "bento_cards": "Gunakan Card dengan header ringkas + konten padat; radius 12px; shadow halus"
  },
  "components": {
    "component_path": {
      "navigation": ["/app/frontend/src/components/ui/navigation-menu.jsx", "/app/frontend/src/components/ui/breadcrumb.jsx"],
      "inputs": ["/app/frontend/src/components/ui/input.jsx", "/app/frontend/src/components/ui/textarea.jsx", "/app/frontend/src/components/ui/label.jsx", "/app/frontend/src/components/ui/select.jsx"],
      "actions": ["/app/frontend/src/components/ui/button.jsx", "/app/frontend/src/components/ui/sonner.jsx"],
      "structure": ["/app/frontend/src/components/ui/card.jsx", "/app/frontend/src/components/ui/separator.jsx", "/app/frontend/src/components/ui/skeleton.jsx"],
      "overlays": ["/app/frontend/src/components/ui/dialog.jsx", "/app/frontend/src/components/ui/drawer.jsx", "/app/frontend/src/components/ui/sheet.jsx", "/app/frontend/src/components/ui/tooltip.jsx"],
      "selection": ["/app/frontend/src/components/ui/radio-group.jsx", "/app/frontend/src/components/ui/toggle-group.jsx"],
      "data_display": ["/app/frontend/src/components/ui/badge.jsx", "/app/frontend/src/components/ui/table.jsx", "/app/frontend/src/components/ui/tabs.jsx"],
      "calendar_if_needed": ["/app/frontend/src/components/ui/calendar.jsx"]
    },
    "header_nav": {
      "pattern": "Sticky top bar + search + tombol Keranjang dengan badge qty",
      "classes": [
        "sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80",
        "h-14 flex items-center gap-3"
      ],
      "elements": [
        {"name": "Brand", "testid": "app-brand"},
        {"name": "Search input", "testid": "product-search-input"},
        {"name": "Cart button", "testid": "open-cart-button"},
        {"name": "Login", "testid": "customer-login-link"}
      ]
    },
    "category_chips": {
      "component": "ToggleGroup (type=single) atau ScrollArea + Button variant=secondary",
      "classes": [
        "flex gap-2 overflow-x-auto py-2",
        "[&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
      ],
      "chip": {
        "base": "rounded-full px-3 py-1 text-sm",
        "active": "bg-accent text-accent-foreground border border-border",
        "inactive": "bg-secondary text-secondary-foreground border border-border hover:bg-muted"
      },
      "testid": "category-chip"
    },
    "product_card": {
      "component": "Card + AspectRatio (image) + Button + qty stepper",
      "layout": "Image top (1:1), title, meta row (unit + MOQ), price, add-to-cart row",
      "classes": {
        "card": "group overflow-hidden border bg-card shadow-sm hover:shadow-md transition-shadow",
        "imageWrap": "bg-muted",
        "title": "line-clamp-2",
        "meta": "mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground",
        "price": "mt-2 font-display text-base font-semibold",
        "ctaRow": "mt-3 flex items-center gap-2"
      },
      "qty_stepper": {
        "pattern": "- / qty / + dengan Button size=icon + Input kecil readOnly",
        "rules": ["Step mengikuti unit (mis. 1 kg) dan enforce MOQ"],
        "testids": {
          "decrease": "cart-qty-decrease-button",
          "increase": "cart-qty-increase-button",
          "value": "cart-qty-value"
        }
      },
      "testids": {
        "card": "product-card",
        "add": "add-to-cart-button",
        "image": "product-image",
        "name": "product-name",
        "price": "product-price"
      }
    },
    "cart": {
      "pattern": "Mobile: Drawer/Sheet; Desktop: halaman /keranjang",
      "components": ["Sheet atau Drawer", "Table untuk ringkasan", "Separator"],
      "line_item": {
        "layout": "thumbnail + nama + unit/MOQ + stepper + subtotal",
        "testids": {
          "remove": "cart-remove-item-button",
          "checkout": "cart-checkout-button"
        }
      },
      "empty_state": {
        "copy": "Keranjang masih kosong. Pilih produk untuk mulai belanja.",
        "cta": "Kembali ke Beranda",
        "testid": "cart-empty-state"
      }
    },
    "checkout": {
      "layout": "2 kolom di desktop: Form (kiri) + Ringkasan (kanan). Mobile: stack.",
      "form_fields": [
        {"label": "Nama Lengkap", "placeholder": "Contoh: SPPG Dapur Melati", "testid": "checkout-full-name-input"},
        {"label": "No. Telp/WA", "placeholder": "08xxxxxxxxxx", "testid": "checkout-phone-input"},
        {"label": "Alamat", "placeholder": "Nama jalan, kecamatan, kota/kabupaten", "testid": "checkout-address-textarea"},
        {"label": "Catatan (opsional)", "placeholder": "Contoh: Kirim pagi sebelum jam 09.00", "testid": "checkout-notes-textarea"}
      ],
      "identity_note": "Tampilkan helper text: 'Nama Lengkap akan digunakan sebagai ID login untuk melihat riwayat pesanan.'",
      "testids": {
        "submit": "checkout-submit-button",
        "summary": "checkout-order-summary"
      }
    },
    "payment_method_selection": {
      "component": "RadioGroup + Card clickable",
      "methods": [
        {"key": "cod", "title": "COD", "desc": "Bayar saat barang diterima", "icon": "Truck", "testid": "payment-method-cod"},
        {"key": "bank_transfer", "title": "Transfer Bank", "desc": "Virtual Account / verifikasi otomatis (Midtrans/Xendit)", "icon": "Landmark", "testid": "payment-method-bank-transfer"},
        {"key": "qris", "title": "QRIS", "desc": "Scan QR untuk bayar (sementara: gambar statis)", "icon": "QrCode", "testid": "payment-method-qris"},
        {"key": "ewallet", "title": "E-Wallet", "desc": "GoPay / OVO / DANA / ShopeePay", "icon": "Wallet", "testid": "payment-method-ewallet"}
      ],
      "card_classes": {
        "base": "relative flex items-start gap-3 rounded-xl border bg-card p-4 shadow-sm",
        "hover": "hover:bg-muted/40 transition-colors",
        "selected": "ring-2 ring-ring"
      }
    },
    "payment_instruction_page": {
      "pattern": "Step-by-step instructions + status badge + tombol 'Simulasi Bayar' (sandbox) + polling indicator",
      "components": ["Badge", "Card", "Progress (optional)", "Skeleton"],
      "qris_placeholder": "Gunakan Card dengan gambar QR statis + tombol 'Unduh QR' (disabled) untuk sekarang.",
      "testids": {
        "status": "payment-status-badge",
        "simulate": "payment-simulate-button",
        "qris": "payment-qris-image"
      }
    },
    "order_history": {
      "pattern": "List cards di mobile, Table di desktop",
      "status_badge": "Gunakan Badge variant=secondary + semantic_status_colors mapping",
      "testids": {
        "list": "order-history-list",
        "item": "order-history-item"
      }
    },
    "admin": {
      "navigation": "Sidebar (desktop) + bottom nav (mobile admin) opsional; tahap 1 cukup top tabs",
      "tables": {
        "component": "Table",
        "features": ["sortable headers (later)", "row actions via DropdownMenu", "empty state"],
        "testids": {
          "products": "admin-products-table",
          "categories": "admin-categories-table",
          "orders": "admin-orders-table"
        }
      },
      "dialogs": {
        "component": "Dialog",
        "usage": "CRUD Kategori/Produk (nama, harga, unit, MOQ, image URL)",
        "testid": "admin-crud-dialog"
      },
      "kpi_cards": {
        "component": "Card",
        "layout": "grid grid-cols-2 lg:grid-cols-4 gap-3",
        "testid": "admin-kpi-card"
      }
    }
  },
  "motion_and_microinteractions": {
    "principles": [
      "Hover: hanya shadow/warna border (transition-shadow/transition-colors)",
      "Press: tombol scale-[0.98] via active:scale-[0.98] (tanpa transition all)",
      "Loading: Skeleton untuk grid produk & tabel admin",
      "Scroll: category chips sticky di bawah navbar saat scroll (optional)"
    ],
    "recommended_library": {
      "name": "framer-motion",
      "why": "Entrance animation halus untuk cards, drawer, dan empty state",
      "install": "npm i framer-motion",
      "usage_snippet_js": "import { motion } from 'framer-motion';\n\nexport default function ProductGrid({ children }) {\n  return (\n    <motion.div\n      initial={{ opacity: 0, y: 8 }}\n      animate={{ opacity: 1, y: 0 }}\n      transition={{ duration: 0.25 }}\n      className=\"grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4\"\n      data-testid=\"product-grid\"\n    >\n      {children}\n    </motion.div>\n  );\n}"
    }
  },
  "accessibility": {
    "rules": [
      "Semua input punya Label (shadcn Label) dan helper/error text.",
      "Focus ring jelas: gunakan ring-ring + ring-offset-background.",
      "Target sentuh min 44px untuk tombol utama/stepper.",
      "Kontras teks: gunakan text-foreground untuk konten utama; muted hanya untuk meta.",
      "Gunakan aria-label untuk tombol ikon (tambah/kurang/hapus)."
    ]
  },
  "images": {
    "image_urls": [
      {
        "category": "hero",
        "description": "Gudang/logistik bahan baku (trust B2B)",
        "url": "https://images.unsplash.com/photo-1570086625846-f33f679eb4f5?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMHByb2R1Y2UlMjB3aG9sZXNhbGUlMjB3YXJlaG91c2V8ZW58MHx8fGdyZWVufDE3ODg4MDgwODB8MA&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "category_banner",
        "description": "Fresh produce field (kategori sayur/buah)",
        "url": "https://images.unsplash.com/photo-1533321942807-08e4008b2025?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHw0fHxmcmVzaCUyMHByb2R1Y2UlMjB3aG9sZXNhbGUlMjB3YXJlaG91c2V8ZW58MHx8fGdyZWVufDE3ODg4MDgwODB8MA&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "trust_section",
        "description": "Operator/quality check (kesan higienis & profesional)",
        "url": "https://images.unsplash.com/photo-1580982325236-11d214b9f279?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NzF8MHwxfHNlYXJjaHwxfHxmb29kJTIwbG9naXN0aWNzJTIwd2FyZWhvdXNlJTIwd29ya2VyJTIwcGFja2luZ3xlbnwwfHx8d2hpdGV8MTc4ODgwODA4NXww&ixlib=rb-4.1.0&q=85"
      }
    ],
    "product_images": {
      "rule": "Tahap 1: gunakan image URL per produk (admin input). Jika kosong, fallback ke placeholder solid bg-muted + ikon Package.",
      "placeholder": "Gunakan div bg-muted dengan AspectRatio 1/1 dan ikon lucide-react 'Package'"
    },
    "qris_placeholder": {
      "rule": "Gunakan gambar QR statis sementara (asset lokal).",
      "path_suggestion": "/app/frontend/src/assets/qris-placeholder.png",
      "testid": "qris-placeholder-image"
    }
  },
  "css_tokens_and_utilities": {
    "global_css": {
      "index_css_changes": [
        "Set body font ke Manrope dan heading pakai font-display via utility class.",
        "Tambahkan selection color: selection:bg-accent selection:text-accent-foreground.",
        "Tambahkan subtle noise overlay optional via background-image (jangan mengganggu readability)."
      ],
      "noise_snippet": "/* optional subtle noise */\n.noise-bg {\n  background-image: url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"120\" height=\"120\"><filter id=\"n\"><feTurbulence type=\"fractalNoise\" baseFrequency=\"0.9\" numOctaves=\"2\" stitchTiles=\"stitch\"/></filter><rect width=\"120\" height=\"120\" filter=\"url(%23n)\" opacity=\"0.06\"/></svg>');\n  background-repeat: repeat;\n}"
    },
    "buttons": {
      "shape": "Rounded corners 10–12px (radius token 0.75rem)",
      "variants": {
        "primary": "Button default (bg-primary text-primary-foreground) + hover:bg-primary/90",
        "secondary": "Button variant=secondary untuk chip/aksi minor",
        "ghost": "Button variant=ghost untuk row actions"
      },
      "interaction_classes": [
        "active:scale-[0.98]",
        "transition-colors transition-shadow"
      ]
    },
    "inputs": {
      "classes": [
        "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "placeholder:text-muted-foreground/70"
      ]
    }
  },
  "data_testid_conventions": {
    "rule": "Semua elemen interaktif & info penting wajib punya data-testid (kebab-case, berbasis peran).",
    "examples": [
      "data-testid=\"product-search-input\"",
      "data-testid=\"add-to-cart-button\"",
      "data-testid=\"checkout-submit-button\"",
      "data-testid=\"payment-status-badge\"",
      "data-testid=\"admin-products-table\""
    ]
  },
  "instructions_to_main_agent": [
    "Update /app/frontend/src/App.css: hapus styling CRA default (App-header center/dark). Jangan set text-align center pada container.",
    "Update /app/frontend/src/index.css tokens (:root) sesuai tokens_hsl di atas; pertahankan struktur shadcn.",
    "Tambahkan Google Fonts (Space Grotesk + Manrope) via index.html atau CSS import; set font-sans default ke Manrope.",
    "Implement Beranda: navbar sticky + search + category chips (horizontal scroll) + section per kategori + product card grid.",
    "Product card wajib tampilkan: nama, gambar, harga/unit, unit, MOQ, stepper qty, tombol Tambah.",
    "Keranjang: gunakan Sheet/Drawer untuk mobile quick view + halaman /keranjang untuk edit detail.",
    "Checkout: form + ringkasan; helper text untuk 'Nama Lengkap jadi ID login'.",
    "Pembayaran: RadioGroup card untuk metode; halaman instruksi per metode + status badge + polling + tombol simulasi.",
    "Admin (tahap berikut): gunakan Table + Dialog CRUD; KPI cards.",
    "Pastikan semua tombol/input/link/status penting punya data-testid.",
    "Gunakan lucide-react icons: ShoppingCart, Search, Package, Truck, Landmark, QrCode, Wallet, CheckCircle2, AlertTriangle."
  ],
  "web_inspiration_notes": {
    "references": [
      {
        "topic": "B2B wholesale patterns (chips, tiered pricing, admin tables)",
        "source": "https://www.rocket.new/templates/provisions-premium-wholesale-landing-page-template"
      },
      {
        "topic": "Bulk checkout layout idea (table-like summary)",
        "source": "https://www.shadcn.io/blocks/checkout-bulk-order"
      }
    ]
  },
  "general_ui_ux_design_guidelines_appendix": "- You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
}
