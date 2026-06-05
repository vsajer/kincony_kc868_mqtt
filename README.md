# KinCony KC868 MQTT Controller

Univerzální Home Assistant integrace pro desky KinCony KC868 běžící přes MQTT.

Integrace je navržená pro firmware, který posílá kompletní JSON stav na topicu typu:

```text
KC868_A16/ECC9FF002428/STATE
```

a přijímá příkazy na topicu typu:

```text
KC868_A16/ECC9FF002428/SET
```

## Co umí

- Přidání přes UI v Home Assistantu.
- Po zadání MQTT prefixu počká na první `STATE` zprávu.
- Automaticky zjistí počet:
  - `input*`
  - `output*`
  - `adc*`
  - `sensor*`
- Vytvoří jedno zařízení v HA.
- Umožní ručně upravit mapování kanálů přes JSON.
- Podporované typy:
  - vstupy: `binary_sensor`
  - výstupy: `switch`, `light`, `button`
  - ADC / teplota / vlhkost: `sensor`
- Příkazy na `SET` posílá vždy s `retain: false`.
- Stav čte z retained `STATE`, takže po restartu HA naskočí poslední známý stav.

## Co záměrně neumí

- Nevytváří `cover` entity pro vrata.
- Nepoužívá HTTP API.
- Nepředpokládá pevně KC868-A16; počet I/O bere z přijatého JSON.

## Instalace přes HACS

1. HACS → Integrations → Custom repositories.
2. Přidej URL repozitáře.
3. Kategorie: Integration.
4. Nainstaluj `KinCony KC868 MQTT Controller`.
5. Restartuj Home Assistant.
6. Nastavení → Zařízení a služby → Přidat integraci → KinCony KC868 MQTT Controller.

## Ruční instalace

Zkopíruj složku:

```text
custom_components/kincony_kc868_mqtt
```

do:

```text
/config/custom_components/kincony_kc868_mqtt
```

Restartuj Home Assistant.

## Konfigurace

Příklad pro tvoji desku:

```text
Název zařízení: KC868-A16 Garáž
IP adresa: volitelné
Model: KC868-A16
MQTT prefix: KC868_A16/ECC9FF002428
State topic: nech prázdné, doplní se KC868_A16/ECC9FF002428/STATE
Command topic: nech prázdné, doplní se KC868_A16/ECC9FF002428/SET
Refresh payload: nech prázdné
```

Integrace poté počká na retained `STATE` zprávu a nabídne JSON mapování.

## Příklad mapování

```json
{
  "inputs": {
    "input1": {
      "enabled": true,
      "name": "G1 Vrata Zavřená",
      "type": "binary_sensor",
      "device_class": "garage_door",
      "invert": false,
      "icon": "mdi:garage-variant-lock"
    },
    "input2": {
      "enabled": true,
      "name": "G1 Vrata Otevřená",
      "type": "binary_sensor",
      "device_class": "garage_door",
      "invert": false,
      "icon": "mdi:garage-open-variant"
    },
    "input7": {
      "enabled": true,
      "name": "G1 Auto v Garáži",
      "type": "binary_sensor",
      "device_class": "occupancy",
      "invert": true,
      "icon": "mdi:car"
    }
  },
  "outputs": {
    "output1": {
      "enabled": true,
      "name": "G1 Otevřít",
      "type": "button",
      "device_class": "none",
      "invert": false,
      "icon": "mdi:garage-open-variant",
      "pulse_seconds": 0.5
    },
    "output12": {
      "enabled": true,
      "name": "G1 Světlo Přední",
      "type": "light",
      "device_class": "none",
      "invert": false,
      "icon": ""
    },
    "output16": {
      "enabled": true,
      "name": "Zásuvka Nabíječka",
      "type": "switch",
      "device_class": "outlet",
      "invert": false,
      "icon": ""
    }
  },
  "sensors": {}
}
```

## Důležité k MQTT retain

Dobře:

```text
KC868_A16/.../STATE  retain=true
```

Špatně:

```text
KC868_A16/.../SET    retain=true
```

Stav má být uložený v brokeru. Příkaz ne. U vrat a relé by retained příkaz mohl po reconnectu zopakovat starý povel.

## Vývojový stav

Verze `0.1.0` je první testovací verze. Je určená k ověření architektury, mapování I/O a entity modelu.
