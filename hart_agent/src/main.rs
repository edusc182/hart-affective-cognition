use crossbeam_channel::unbounded;
use llama_cpp_2::context::params::LlamaContextParams;
use llama_cpp_2::llama_backend::LlamaBackend;
use llama_cpp_2::llama_batch::LlamaBatch;
use llama_cpp_2::model::params::LlamaModelParams;
use llama_cpp_2::model::{AddBos, LlamaModel};
use llama_cpp_2::sampling::LlamaSampler;
use serde::{Deserialize, Serialize};
use std::io::{self, Write};
use std::num::NonZeroU32;
use std::path::PathBuf;
use std::thread;
use std::time::Duration;
use encoding_rs::UTF_8;

#[derive(Debug, Clone)]
struct Percepcion {
    luz: String,
    distancia: f32,
    mensaje_usuario: Option<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct RespuestaCognitiva {
    comando_fisico: String,
    valencia: f32,
    tension_facial: f32,
    dialogo_hablado: String,
}

fn main() {
    println!("Iniciando HART Consciousness Model en Rust...");

    let model_path = resolve_model_path();
    println!("[BOOT] GGUF configurado en: {}", model_path.display());

    let (tx_percepcion, rx_percepcion) = unbounded::<Percepcion>();
    let (tx_cognicion, rx_cognicion) = unbounded::<RespuestaCognitiva>();

    thread::spawn(move || {
        let backend = match LlamaBackend::init() {
            Ok(backend) => backend,
            Err(err) => {
                eprintln!("[CEREBRO] No se pudo iniciar llama backend: {err}");
                return;
            }
        };

        // CPU-only: no offload de capas a GPU.
        let model_params = LlamaModelParams::default().with_n_gpu_layers(0);

        let model = match LlamaModel::load_from_file(&backend, &model_path, &model_params) {
            Ok(model) => model,
            Err(err) => {
                eprintln!("[CEREBRO] Error cargando GGUF: {err}");
                return;
            }
        };

        println!("[CEREBRO] Modelo GGUF cargado en CPU.");

        while let Ok(percepcion) = rx_percepcion.recv() {
            println!("[CEREBRO] Nueva percepción recibida; inferencia en curso...");
            let respuesta = inferir_respuesta(&backend, &model, &percepcion)
                .unwrap_or_else(|err| fallback_response(err.as_str()));

            if tx_cognicion.send(respuesta).is_err() {
                break;
            }
        }
    });

    let mut valencia_actual = 0.0_f32;
    let mut tension_actual = 0.0_f32;
    let mut frame_count = 0_u64;
    let mut perception_step = 0_u64;

    let _ = tx_percepcion.send(next_autonomous_perception(perception_step, valencia_actual, tension_actual));

    loop {
        if let Ok(nueva_cognicion) = rx_cognicion.try_recv() {
            println!("\n--- NUEVO ESTADO COGNITIVO ---");
            println!("ACCION: {}", nueva_cognicion.comando_fisico);
            println!("VOZ: \"{}\"", nueva_cognicion.dialogo_hablado);

            valencia_actual = nueva_cognicion.valencia;
            tension_actual = nueva_cognicion.tension_facial;
            perception_step += 1;

            let _ = tx_percepcion.send(next_autonomous_perception(
                perception_step,
                valencia_actual,
                tension_actual,
            ));
        }

        if frame_count % 60 == 0 {
            println!(
                "[CUERPO] Latiendo... Valencia: {:.2} | Tension: {:.2}",
                valencia_actual, tension_actual
            );
        }

        thread::sleep(Duration::from_millis(16));
        frame_count += 1;
    }
}

fn resolve_model_path() -> PathBuf {
    if let Ok(path) = std::env::var("HART_GGUF_PATH") {
        return PathBuf::from(path);
    }

    if let Some(arg) = std::env::args().nth(1) {
        return PathBuf::from(arg);
    }

    PathBuf::from("model.gguf")
}

fn next_autonomous_perception(step: u64, valencia_actual: f32, tension_actual: f32) -> Percepcion {
    let stage = step % 5;

    match stage {
        0 => Percepcion {
            luz: "Bajo".to_string(),
            distancia: if valencia_actual < -0.2 { 3.2 } else { 2.6 },
            mensaje_usuario: Some("No detecto voces; solo un zumbido electrico lejano.".to_string()),
        },
        1 => Percepcion {
            luz: "Alto".to_string(),
            distancia: 0.8,
            mensaje_usuario: Some("Hay un objeto rojo muy cerca del campo visual.".to_string()),
        },
        2 => Percepcion {
            luz: "Medio".to_string(),
            distancia: 1.4,
            mensaje_usuario: Some("Se escucha un golpe metalico detras de la puerta.".to_string()),
        },
        3 => Percepcion {
            luz: if tension_actual > 0.35 { "Bajo" } else { "Medio" }.to_string(),
            distancia: 2.1,
            mensaje_usuario: Some("Un operador solicita evaluar la zona antes de avanzar.".to_string()),
        },
        _ => Percepcion {
            luz: "Alto".to_string(),
            distancia: if valencia_actual > 0.25 { 1.0 } else { 1.8 },
            mensaje_usuario: Some("El entorno parece estable, pero hay movimiento periferico.".to_string()),
        },
    }
}

fn inferir_respuesta(
    backend: &LlamaBackend,
    model: &LlamaModel,
    percepcion: &Percepcion,
) -> Result<RespuestaCognitiva, String> {
    let prompt = build_prompt(percepcion);

    let mut ctx_params =
        LlamaContextParams::default().with_n_ctx(Some(NonZeroU32::new(2048).expect("n_ctx inválido")));
    ctx_params = ctx_params.with_n_batch(512);

    let mut ctx = model
        .new_context(backend, ctx_params)
        .map_err(|err| format!("No se pudo crear contexto llama: {err}"))?;

    let tokens = model
        .str_to_token(&prompt, AddBos::Always)
        .map_err(|err| format!("Tokenización falló: {err}"))?;

    if tokens.is_empty() {
        return Err("Prompt vacío tras tokenización".to_string());
    }

    let mut batch = LlamaBatch::new(512, 1);
    let last_index = (tokens.len() - 1) as i32;
    for (i, token) in (0_i32..).zip(tokens.into_iter()) {
        batch
            .add(token, i, &[0], i == last_index)
            .map_err(|err| format!("No se pudo preparar batch: {err}"))?;
    }

    ctx.decode(&mut batch)
        .map_err(|err| format!("Decode inicial falló: {err}"))?;

    let mut decoder = UTF_8.new_decoder();

    // JSON estricto: greedy reduce alucinaciones de formato.
    let mut sampler = LlamaSampler::chain_simple([LlamaSampler::greedy()]);

    let mut generated = String::new();
    let mut n_cur = batch.n_tokens();
    let max_new_tokens = 256;
    eprintln!("[DEBUG] Iniciando generacion de tokens...");

    for _ in 0..max_new_tokens {
        let token = sampler.sample(&ctx, batch.n_tokens() - 1);
        sampler.accept(token);

        if model.is_eog_token(token) {
            break;
        }

        let token_str = model.token_to_piece(token, &mut decoder, true, None).unwrap_or_default();

        print!("{}", token_str);
        io::stdout().flush().unwrap();
        eprintln!("[TOKEN] {} bytes", token_str.len());

        generated.push_str(&token_str);

        batch.clear();
        batch
            .add(token, n_cur, &[0], true)
            .map_err(|err| format!("No se pudo agregar token generado: {err}"))?;
        n_cur += 1;

        ctx.decode(&mut batch)
            .map_err(|err| format!("Decode incremental falló: {err}"))?;
    }

    let normalized = normalize_model_output(&generated);
    let json_payload = extract_first_json_object(&normalized)
        .or_else(|| maybe_wrap_json_body(&normalized))
        .or_else(|| extract_first_json_object(&generated))
        .or_else(|| maybe_wrap_json_body(&generated))
        .ok_or_else(|| {
            format!(
                "El modelo no devolvió JSON válido. Salida normalizada: {}",
                normalized
            )
        })?;

    serde_json::from_str::<RespuestaCognitiva>(&json_payload)
        .map_err(|err| format!("JSON cognitivo inválido: {err}. Payload: {json_payload}"))
}

fn build_prompt(percepcion: &Percepcion) -> String {
    let mensaje_usuario = percepcion
        .mensaje_usuario
        .clone()
        .unwrap_or_else(|| "(sin input de voz)".to_string());

    format!(
        "<start_of_turn>user\n\
Eres Sujeto-01. Responde UNICAMENTE con un JSON valido, sin markdown ni texto fuera del objeto.\n\
Percepcion actual: Luz={}, Distancia={:.3}m, MensajeUsuario='{}'.\n\
Esquema exacto:\n\
{{\n\
  \"comando_fisico\": \"accion\",\n\
  \"valencia\": 0.0,\n\
  \"tension_facial\": 0.0,\n\
  \"dialogo_hablado\": \"texto\"\n\
}}\n\
<end_of_turn>\n\
<start_of_turn>model\n{{",
        percepcion.luz, percepcion.distancia, mensaje_usuario
    )
}

fn normalize_model_output(raw: &str) -> String {
    raw.replace("```json", "")
        .replace("```", "")
        .replace("<end_of_turn>", "")
        .trim()
        .to_string()
}

fn maybe_wrap_json_body(text: &str) -> Option<String> {
    let trimmed = text.trim();

    if trimmed.starts_with('{') || !trimmed.ends_with('}') {
        return None;
    }

    if trimmed.starts_with('"') {
        return Some(format!("{{{trimmed}"));
    }

    None
}

fn extract_first_json_object(text: &str) -> Option<String> {
    let mut depth = 0_i32;
    let mut start = None;
    for (index, ch) in text.char_indices() {
        if ch == '{' {
            if depth == 0 {
                start = Some(index);
            }
            depth += 1;
        } else if ch == '}' {
            depth -= 1;
            if depth == 0 {
                if let Some(start_index) = start {
                    return Some(text[start_index..=index].to_string());
                }
            }
            if depth < 0 {
                return None;
            }
        }
    }
    None
}

fn fallback_response(error_reason: &str) -> RespuestaCognitiva {
    eprintln!("[CEREBRO] Fallback cognitivo por error: {error_reason}");
    RespuestaCognitiva {
        comando_fisico: "Mantener posicion y escanear entorno".to_string(),
        valencia: -0.2,
        tension_facial: 0.4,
        dialogo_hablado: "No pude consolidar una inferencia estable; mantengo postura cautelosa.".to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::{extract_first_json_object, maybe_wrap_json_body};

    #[test]
    fn wraps_json_body_missing_opening_brace() {
        let raw = "\"comando_fisico\":\"observar\",\"valencia\":0.0,\"tension_facial\":0.0,\"dialogo_hablado\":\"ok\"}";

        let repaired = maybe_wrap_json_body(raw).expect("debe reparar cuerpo JSON truncado");

        assert_eq!(
            repaired,
            "{\"comando_fisico\":\"observar\",\"valencia\":0.0,\"tension_facial\":0.0,\"dialogo_hablado\":\"ok\"}"
        );
    }

    #[test]
    fn extracts_regular_json_object_without_repair() {
        let raw = "ruido {\"comando_fisico\":\"observar\",\"valencia\":0.0,\"tension_facial\":0.0,\"dialogo_hablado\":\"ok\"} final";

        let extracted = extract_first_json_object(raw).expect("debe extraer un objeto JSON completo");

        assert_eq!(
            extracted,
            "{\"comando_fisico\":\"observar\",\"valencia\":0.0,\"tension_facial\":0.0,\"dialogo_hablado\":\"ok\"}"
        );
    }
}
