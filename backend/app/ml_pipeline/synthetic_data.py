from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


RANDOM_STATE = 42
TRAINING_ROWS = 15000


@dataclass(frozen=True)
class ClassConfig:
    temperature_mean: float
    temperature_std: float
    temperature_rate_mean: float
    temperature_rate_std: float
    smoke_mean: float
    smoke_std: float
    co_mean: float
    co_std: float
    co2_mean: float
    co2_std: float
    humidity_mean: float
    humidity_std: float
    electrical_mean: float
    electrical_std: float
    occupancy_mean: float
    occupancy_std: float
    hvac_prob: float
    sprinkler_prob: float


_CLASS_CONFIG: dict[str, ClassConfig] = {
    "NORMAL": ClassConfig(
        temperature_mean=25.5,
        temperature_std=3.8,
        temperature_rate_mean=0.08,
        temperature_rate_std=0.09,
        smoke_mean=0.035,
        smoke_std=0.018,
        co_mean=4.8,
        co_std=1.8,
        co2_mean=515.0,
        co2_std=90.0,
        humidity_mean=52.0,
        humidity_std=9.0,
        electrical_mean=44.0,
        electrical_std=11.0,
        occupancy_mean=66.0,
        occupancy_std=28.0,
        hvac_prob=0.88,
        sprinkler_prob=0.01,
    ),
    "WARNING": ClassConfig(
        temperature_mean=40.5,
        temperature_std=11.5,
        temperature_rate_mean=0.55,
        temperature_rate_std=0.42,
        smoke_mean=0.22,
        smoke_std=0.14,
        co_mean=16.0,
        co_std=9.8,
        co2_mean=820.0,
        co2_std=260.0,
        humidity_mean=43.0,
        humidity_std=12.0,
        electrical_mean=66.0,
        electrical_std=18.0,
        occupancy_mean=82.0,
        occupancy_std=35.0,
        hvac_prob=0.8,
        sprinkler_prob=0.14,
    ),
    "CRITICAL": ClassConfig(
        temperature_mean=66.0,
        temperature_std=17.5,
        temperature_rate_mean=1.45,
        temperature_rate_std=0.78,
        smoke_mean=0.56,
        smoke_std=0.24,
        co_mean=35.0,
        co_std=15.0,
        co2_mean=1280.0,
        co2_std=320.0,
        humidity_mean=34.0,
        humidity_std=12.0,
        electrical_mean=79.0,
        electrical_std=17.0,
        occupancy_mean=96.0,
        occupancy_std=38.0,
        hvac_prob=0.69,
        sprinkler_prob=0.62,
    ),
}


def _clip_binary(array: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    return (array > threshold).astype(int)


def _clipped(values: np.ndarray, low: float, high: float) -> np.ndarray:
    return np.clip(values, low, high)


def _inject_sensor_noise(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    noisy = df.copy()

    elevated_temp_without_fire = rng.random(len(noisy)) < 0.075
    noisy.loc[elevated_temp_without_fire, "temperature"] += rng.normal(8.0, 2.5, elevated_temp_without_fire.sum())
    noisy.loc[elevated_temp_without_fire, "smoke_level"] += rng.normal(0.0, 0.01, elevated_temp_without_fire.sum())
    noisy.loc[elevated_temp_without_fire, "co_level"] += rng.normal(0.2, 0.4, elevated_temp_without_fire.sum())

    smoke_noise = rng.random(len(noisy)) < 0.14
    noisy.loc[smoke_noise, "smoke_level"] += rng.gamma(shape=1.2, scale=0.03, size=smoke_noise.sum())

    electrical_spike = rng.random(len(noisy)) < 0.12
    noisy.loc[electrical_spike, "electrical_load"] += rng.normal(12.0, 5.0, electrical_spike.sum())

    sensor_inconsistency = rng.random(len(noisy)) < 0.06
    noisy.loc[sensor_inconsistency, "temperature"] += rng.normal(7.0, 3.0, sensor_inconsistency.sum())
    noisy.loc[sensor_inconsistency, "co_level"] -= rng.normal(1.6, 0.8, sensor_inconsistency.sum())
    noisy.loc[sensor_inconsistency, "smoke_level"] -= rng.normal(0.03, 0.02, sensor_inconsistency.sum())

    noisy["temperature"] = _clipped(noisy["temperature"].to_numpy(), 12.0, 130.0)
    noisy["temperature_rate"] = _clipped(noisy["temperature_rate"].to_numpy(), 0.0, 5.0)
    noisy["smoke_level"] = _clipped(noisy["smoke_level"].to_numpy(), 0.0, 1.0)
    noisy["co_level"] = _clipped(noisy["co_level"].to_numpy(), 0.0, 120.0)
    noisy["co2_level"] = _clipped(noisy["co2_level"].to_numpy(), 350.0, 3500.0)
    noisy["humidity"] = _clipped(noisy["humidity"].to_numpy(), 5.0, 95.0)
    noisy["electrical_load"] = _clipped(noisy["electrical_load"].to_numpy(), 5.0, 100.0)
    noisy["occupancy"] = _clipped(noisy["occupancy"].to_numpy(), 0.0, 200.0)

    return noisy


def generate_synthetic_fire_dataset(rows: int = TRAINING_ROWS, random_state: int = RANDOM_STATE) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    classes = np.array(["NORMAL", "WARNING", "CRITICAL"])
    class_probs = np.array([0.60, 0.25, 0.15])
    sampled = rng.choice(classes, size=rows, p=class_probs)

    # Mild label overlap keeps the academic dataset realistic and not perfectly separable.
    overlap_mask = rng.random(rows) < 0.035
    for idx in np.where(overlap_mask)[0]:
        current = sampled[idx]
        if current == "NORMAL":
            sampled[idx] = "WARNING"
        elif current == "CRITICAL":
            sampled[idx] = "WARNING"
        else:
            sampled[idx] = rng.choice(np.array(["NORMAL", "CRITICAL"]))

    records: list[dict[str, float | int | str]] = []
    for risk_class in sampled:
        cfg = _CLASS_CONFIG[risk_class]

        # Correlated latent hazard factor introduces overlap while preserving physically plausible trends.
        hazard_shift = rng.normal(0.0, 1.0)

        temperature = rng.normal(cfg.temperature_mean + 1.4 * hazard_shift, cfg.temperature_std)
        temperature_rate = rng.normal(cfg.temperature_rate_mean + 0.08 * hazard_shift, cfg.temperature_rate_std)
        smoke_level = rng.normal(cfg.smoke_mean + 0.02 * hazard_shift, cfg.smoke_std)
        co_level = rng.normal(cfg.co_mean + 1.9 * hazard_shift, cfg.co_std)
        co2_level = rng.normal(cfg.co2_mean + 28.0 * hazard_shift, cfg.co2_std)
        humidity = rng.normal(cfg.humidity_mean - 0.8 * hazard_shift, cfg.humidity_std)
        electrical_load = rng.normal(cfg.electrical_mean + 1.1 * hazard_shift, cfg.electrical_std)
        occupancy = rng.normal(cfg.occupancy_mean + 3.0 * hazard_shift, cfg.occupancy_std)

        hvac_running = int(rng.random() < cfg.hvac_prob)
        sprinkler_active = int(rng.random() < cfg.sprinkler_prob)

        records.append(
            {
                "temperature": temperature,
                "temperature_rate": max(0.0, temperature_rate),
                "smoke_level": max(0.0, smoke_level),
                "co_level": max(0.0, co_level),
                "co2_level": max(350.0, co2_level),
                "humidity": humidity,
                "electrical_load": electrical_load,
                "occupancy": occupancy,
                "hvac_running": hvac_running,
                "sprinkler_active": sprinkler_active,
                "risk_class": risk_class,
            }
        )

    dataset = pd.DataFrame.from_records(records)
    dataset = _inject_sensor_noise(dataset, rng)
    dataset["hvac_running"] = _clip_binary(dataset["hvac_running"].to_numpy()).astype(int)
    dataset["sprinkler_active"] = _clip_binary(dataset["sprinkler_active"].to_numpy()).astype(int)

    return dataset
