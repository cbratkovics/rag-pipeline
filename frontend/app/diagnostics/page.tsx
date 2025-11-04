import Hero from "../../components/Hero";
import Diagnostics from "../../components/Diagnostics";

export default function Page() {
  return (
    <main className="min-h-screen bg-gray-50">
      <Hero />
      <div className="mx-auto max-w-5xl px-4 pb-12">
        <Diagnostics />
      </div>
    </main>
  );
}
