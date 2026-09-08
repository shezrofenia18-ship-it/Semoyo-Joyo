import { Outlet } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { CartSheet } from "@/components/CartSheet";
import { FloatingCart } from "@/components/FloatingCart";

export const StoreLayout = () => {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <main className="flex-1 pb-20 sm:pb-0">
        <Outlet />
      </main>
      <Footer />
      <CartSheet />
      <FloatingCart />
    </div>
  );
};
