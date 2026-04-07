import { useEffect, useState } from "react";

const API_URL = "http://37.140.243.39:8000";

function App() {
    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState("");
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState("");
    const [result, setResult] = useState(null);
    const [loadingModels, setLoadingModels] = useState(true);
    const [predicting, setPredicting] = useState(false);
    const [error, setError] = useState("");
    const [settings, setSettings] = useState({
        conf: 0.25,
        iou: 0.45,
        imgsz: 960,
    });
    const [objectQuery, setObjectQuery] = useState("");

    useEffect(() => {
        let isMounted = true;

        async function fetchModels() {
            setLoadingModels(true);
            setError("");
            try {
                const response = await fetch(`${API_URL}/api/models`);
                if (!response.ok) {
                    throw new Error("Не удалось получить список моделей");
                }
                const data = await response.json();
                if (isMounted) {
                    setModels(data);
                    setSelectedModel(data[0]?.name ?? "");
                }
            } catch (requestError) {
                if (isMounted) {
                    setError(requestError.message);
                }
            } finally {
                if (isMounted) {
                    setLoadingModels(false);
                }
            }
        }

        fetchModels();
        return () => {
            isMounted = false;
        };
    }, []);

    useEffect(() => {
        if (!file) {
            setPreviewUrl("");
            return undefined;
        }

        const objectUrl = URL.createObjectURL(file);
        setPreviewUrl(objectUrl);
        return () => URL.revokeObjectURL(objectUrl);
    }, [file]);

    async function handleSubmit(event) {
        event.preventDefault();
        if (!file || !selectedModel) {
            setError("Выберите модель и изображение");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("model_name", selectedModel);
        formData.append("conf", String(settings.conf));
        formData.append("iou", String(settings.iou));
        formData.append("imgsz", String(settings.imgsz));
        formData.append("object_query", objectQuery);

        setPredicting(true);
        setError("");
        setResult(null);

        try {
            const response = await fetch(`${API_URL}/api/predict`, {
                method: "POST",
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail ?? "Ошибка инференса");
            }
            setResult(data);
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setPredicting(false);
        }
    }

    return (
        <div className="app-shell">
            <div className="ambient ambient-left" />
            <div className="ambient ambient-right" />

            <header className="hero">
                <div>
                    <p className="eyebrow">YOLO Web Interface</p>
                    <h1>Control room для ваших моделей</h1>
                    <p className="hero-copy">
                        Загружайте изображение, переключайте веса и сразу
                        смотрите размеченный результат вместе со списком
                        детекций.
                    </p>
                </div>
                <div className="hero-stat">
                    <span>{models.length}</span>
                    <p>моделей найдено в каталоге `/models`</p>
                </div>
            </header>

            <main className="grid">
                <section className="panel form-panel">
                    <form onSubmit={handleSubmit}>
                        <label className="field">
                            <span>Модель</span>
                            <select
                                value={selectedModel}
                                onChange={(event) =>
                                    setSelectedModel(event.target.value)
                                }
                                disabled={loadingModels || models.length === 0}
                            >
                                {models.map((model) => (
                                    <option key={model.name} value={model.name}>
                                        {model.name} ({model.size_mb} MB)
                                    </option>
                                ))}
                            </select>
                        </label>

                        <label className="field">
                            <span>Изображение</span>
                            <input
                                type="file"
                                accept="image/*"
                                onChange={(event) =>
                                    setFile(event.target.files?.[0] ?? null)
                                }
                            />
                        </label>

                        <div className="slider-grid">
                            <label className="field">
                                <span>Запрос по объектам</span>
                                <input
                                    type="text"
                                    placeholder="Например: person, car"
                                    value={objectQuery}
                                    onChange={(event) =>
                                        setObjectQuery(event.target.value)
                                    }
                                />
                                <small className="field-hint">
                                    Можно указать один или несколько классов через
                                    запятую.
                                </small>
                            </label>

                            <label className="field">
                                <span>Confidence: {settings.conf}</span>
                                <input
                                    type="range"
                                    min="0.05"
                                    max="0.95"
                                    step="0.05"
                                    value={settings.conf}
                                    onChange={(event) =>
                                        setSettings((current) => ({
                                            ...current,
                                            conf: Number(event.target.value),
                                        }))
                                    }
                                />
                            </label>

                            <label className="field">
                                <span>IoU: {settings.iou}</span>
                                <input
                                    type="range"
                                    min="0.05"
                                    max="0.95"
                                    step="0.05"
                                    value={settings.iou}
                                    onChange={(event) =>
                                        setSettings((current) => ({
                                            ...current,
                                            iou: Number(event.target.value),
                                        }))
                                    }
                                />
                            </label>

                            <label className="field">
                                <span>Image Size</span>
                                <input
                                    type="number"
                                    min="320"
                                    max="1920"
                                    step="32"
                                    value={settings.imgsz}
                                    onChange={(event) =>
                                        setSettings((current) => ({
                                            ...current,
                                            imgsz: Number(event.target.value),
                                        }))
                                    }
                                />
                            </label>
                        </div>

                        <button
                            className="primary-button"
                            type="submit"
                            disabled={predicting}
                        >
                            {predicting
                                ? "Выполняем инференс..."
                                : "Запустить распознавание"}
                        </button>

                        {error ? (
                            <div className="error-box">{error}</div>
                        ) : null}
                    </form>
                </section>

                <section className="panel image-panel">
                    <div className="panel-header">
                        <h2>Изображение</h2>
                        <p>
                            {previewUrl
                                ? "Исходник слева, результат ниже"
                                : "Загрузите файл для предпросмотра"}
                        </p>
                    </div>

                    <div className="image-stack">
                        <div className="image-card">
                            <h3>Original</h3>
                            {previewUrl ? (
                                <img
                                    src={previewUrl}
                                    alt="Исходное изображение"
                                />
                            ) : (
                                <div className="empty-state">
                                    Нет изображения
                                </div>
                            )}
                        </div>
                        <div className="image-card">
                            <h3>Prediction</h3>
                            {result?.rendered_image ? (
                                <img
                                    src={`data:image/jpeg;base64,${result.rendered_image}`}
                                    alt="Результат предсказания"
                                />
                            ) : (
                                <div className="empty-state">
                                    Результат появится после инференса
                                </div>
                            )}
                        </div>
                    </div>
                </section>

                <section className="panel detections-panel">
                    <div className="panel-header">
                        <h2>Детекции</h2>
                        <p>
                            {result
                                ? `${result.total_detections} объектов, модель ${result.model}`
                                : "Здесь появится список найденных объектов"}
                        </p>
                    </div>

                    {result?.extra?.query_applied ? (
                        <div className="query-summary">
                            <strong>Запрос:</strong>{" "}
                            {result.extra.requested_classes?.join(", ") || "не указан"}
                            <br />
                            <strong>Совпавшие классы:</strong>{" "}
                            {result.extra.matched_classes?.length
                                ? result.extra.matched_classes.join(", ")
                                : "совпадений нет"}
                        </div>
                    ) : null}

                    <div className="detections-list">
                        {result?.detections?.length ? (
                            result.detections.map((detection, index) => (
                                <article
                                    className="detection-card"
                                    key={`${detection.class_id}-${index}`}
                                >
                                    <strong>{detection.class_name}</strong>
                                    <span>
                                        {Math.round(detection.confidence * 100)}
                                        %
                                    </span>
                                    <code>{detection.bbox.join(", ")}</code>
                                </article>
                            ))
                        ) : (
                            <div className="empty-state">
                                {loadingModels
                                    ? "Загружаем модели..."
                                    : result?.extra?.query_applied &&
                                        !result?.extra?.matched_classes?.length
                                      ? "По запросу не найдено классов в выбранной модели"
                                      : "После запуска инференса здесь будет таблица результатов"}
                            </div>
                        )}
                    </div>

                    {result?.extra?.available_classes?.length ? (
                        <div className="classes-cloud">
                            {result.extra.available_classes.map((className) => (
                                <span key={className} className="class-chip">
                                    {className}
                                </span>
                            ))}
                        </div>
                    ) : null}
                </section>
            </main>
        </div>
    );
}

export default App;
