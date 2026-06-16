import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

Deno.serve(async (_req) => {
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  // 1. Leer rueda_ids actuales del puntero
  const { data: puntero, error: errorPuntero } = await supabase
    .from("puntero")
    .select("rueda_ids")
    .eq("id", 1)
    .single();

  if (errorPuntero || !puntero?.rueda_ids) {
    return new Response(JSON.stringify({ error: "No se pudo leer puntero", detail: errorPuntero }), { status: 500 });
  }

  const ids: number[] = puntero.rueda_ids
    .split(",")
    .map((id: string) => parseInt(id.trim()))
    .filter((id: number) => !isNaN(id));

  if (ids.length === 0) {
    return new Response(JSON.stringify({ message: "Rueda vacía, nada que jubilar" }), { status: 200 });
  }

  // 2. Jubilar todas las tarjetas de la rueda (Estado = 4)
  const { error: errorUpdate } = await supabase
    .from("tarjetas")
    .update({ Estado: 4 })
    .in("id", ids);

  if (errorUpdate) {
    return new Response(JSON.stringify({ error: "Error al jubilar tarjetas", detail: errorUpdate }), { status: 500 });
  }

  // 3. Vaciar rueda_ids y resetear posicion_actual en puntero
  const { error: errorPunteroUpdate } = await supabase
    .from("puntero")
    .update({ rueda_ids: "", posicion_actual: 0 })
    .eq("id", 1);

  if (errorPunteroUpdate) {
    return new Response(JSON.stringify({ error: "Error al limpiar puntero", detail: errorPunteroUpdate }), { status: 500 });
  }

  console.log(`✅ Jubiladas automáticamente: tarjetas [${ids.join(", ")}]`);

  return new Response(
    JSON.stringify({ ok: true, jubiladas: ids }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
});
