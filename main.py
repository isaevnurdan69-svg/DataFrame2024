import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# Настройка страницы
st.set_page_config(
    page_title="Прогноз ВУЗов 2024",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Прогноз показателей ВУЗов на 2024 год")
st.markdown("Загрузите данные мониторинга за 2015, 2020, 2021, 2022 годы")

def simple_forecast(df, years_col, values_col):
    """Простой прогноз на основе линейного тренда"""
    if len(df) < 2:
        return None, 0
    
    # Простая линейная регрессия вручную
    x = df[years_col].values
    y = df[values_col].values
    
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    intercept = (sum_y - slope * sum_x) / n
    
    prediction = slope * 2024 + intercept
    return prediction, slope

# Загрузка файлов
uploaded_files = st.file_uploader(
    "Выберите Excel файлы:",
    type=['xlsx', 'xls'],
    accept_multiple_files=True,
    key="file_uploader"
)

if uploaded_files:
    st.success(f"✅ Загружено файлов: {len(uploaded_files)}")
    
    # Показ загруженных файлов
    for i, file in enumerate(uploaded_files):
        st.write(f"{i+1}. {file.name}")

# Кнопка анализа
if uploaded_files and st.button("🚀 Построить прогноз на 2024 год", type="primary"):
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("📁 Загружаем файлы...")
        # Загрузка всех данных
        all_data = []
        year_mapping = {
            '2015': 2014, '2014': 2014,
            '2020': 2019, '2019': 2019, 
            '2021': 2020, '2020': 2020,
            '2022': 2021, '2021': 2021
        }
        
        for file in uploaded_files:
            df = pd.read_excel(file)
            
            # Определяем год данных из названия файла
            data_year = 2021  # по умолчанию
            for year_str, actual_year in year_mapping.items():
                if year_str in file.name:
                    data_year = actual_year
                    break
            
            df['data_year'] = data_year
            all_data.append(df)
        
        progress_bar.progress(30)
        status_text.text("📊 Объединяем данные...")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        progress_bar.progress(50)
        status_text.text("🎯 Анализируем показатели...")
        
        # Находим числовые колонки для анализа
        numeric_cols = combined_df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col != 'data_year']
        
        # Выбираем топ-5 самых заполненных колонок
        col_quality = []
        for col in numeric_cols:
            filled_ratio = combined_df[col].notna().sum() / len(combined_df)
            if filled_ratio > 0.3:  # Хотя бы 30% заполнено
                col_quality.append((col, filled_ratio))
        
        col_quality.sort(key=lambda x: x[1], reverse=True)
        target_columns = [col[0] for col in col_quality[:3]]
        
        progress_bar.progress(70)
        status_text.text("📈 Строим прогнозы...")
        
        # Анализ по ВУЗам
        results = []
        
        if 'VUZ' in combined_df.columns:
            for vuz in combined_df['VUZ'].unique()[:50]:  # Ограничиваем 50 ВУЗами
                vuz_data = combined_df[combined_df['VUZ'] == vuz]
                
                for col in target_columns:
                    # Группируем по годам и усредняем
                    yearly_data = vuz_data.groupby('data_year')[col].mean().reset_index()
                    yearly_data = yearly_data.dropna()
                    
                    if len(yearly_data) >= 2:
                        prediction, trend = simple_forecast(yearly_data, 'data_year', col)
                        
                        if prediction is not None:
                            trend_direction = "📈 Рост" if trend > 0 else "📉 Снижение" if trend < 0 else "➡️ Стабильно"
                            
                            results.append({
                                'ВУЗ': vuz,
                                'Показатель': col,
                                'Прогноз_2024': round(prediction, 2),
                                'Тренд': round(trend, 3),
                                'Направление': trend_direction,
                                'Лет_данных': len(yearly_data)
                            })
        
        progress_bar.progress(90)
        status_text.text("🎨 Готовим отчет...")
        
        # Создаем DataFrame с результатами
        if results:
            results_df = pd.DataFrame(results)
            
            # Очищаем прогресс-бар
            progress_bar.progress(100)
            progress_bar.empty()
            status_text.empty()
            
            # Показываем результаты
            st.subheader("📊 Результаты прогноза на 2024 год")
            
            # Фильтры
            col1, col2 = st.columns(2)
            with col1:
                selected_indicator = st.selectbox(
                    "Выберите показатель:",
                    results_df['Показатель'].unique()
                )
            with col2:
                sort_by = st.selectbox(
                    "Сортировать по:",
                    ['Прогноз_2024', 'Тренд']
                )
            
            # Фильтруем и сортируем данные
            filtered_df = results_df[results_df['Показатель'] == selected_indicator]
            filtered_df = filtered_df.sort_values(sort_by, ascending=False)
            
            st.dataframe(filtered_df.head(20), use_container_width=True)
            
            # Визуализация
            st.subheader("📈 Визуализация прогнозов")
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
            
            # График 1: Топ-10 ВУЗов по прогнозу
            top_10 = filtered_df.head(10).sort_values('Прогноз_2024')
            ax1.barh(top_10['ВУЗ'], top_10['Прогноз_2024'], color='lightblue')
            ax1.set_xlabel('Прогноз на 2024 год')
            ax1.set_title(f'Топ-10 ВУЗов по {selected_indicator}')
            
            # График 2: Распределение трендов
            ax2.hist(filtered_df['Тренд'], bins=15, alpha=0.7, color='lightcoral', edgecolor='black')
            ax2.axvline(x=0, color='red', linestyle='--', label='Нет изменений')
            ax2.set_xlabel('Изменение в год')
            ax2.set_ylabel('Количество ВУЗов')
            ax2.set_title('Распределение трендов')
            ax2.legend()
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Статистика
            st.subheader("📋 Статистика прогноза")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_forecast = filtered_df['Прогноз_2024'].mean()
                st.metric("Средний прогноз", f"{avg_forecast:.1f}")
            with col2:
                max_forecast = filtered_df['Прогноз_2024'].max()
                st.metric("Максимальный прогноз", f"{max_forecast:.1f}")
            with col3:
                growth_count = len(filtered_df[filtered_df['Тренд'] > 0])
                st.metric("ВУЗов с ростом", growth_count)
            with col4:
                avg_trend = filtered_df['Тренд'].mean()
                st.metric("Средний тренд", f"{avg_trend:.3f}")
            
            # Выводы
            st.subheader("📝 Выводы и обоснование")
            
            if avg_trend > 0.1:
                conclusion = "Наблюдается положительная динамика показателей"
                reason = "Возможные причины: улучшение качества образования, рост популярности ВУЗов"
            elif avg_trend > -0.1:
                conclusion = "Показатели остаются стабильными" 
                reason = "Ситуация в высшем образовании относительно стабильна"
            else:
                conclusion = "Наблюдается негативная тенденция"
                reason = "Возможные причины: демографические изменения, конкуренция"
            
            st.info(f"""
            **{conclusion}**
            
            **Обоснование:** {reason}
            
            **Методология прогноза:**
            - Использованы данные за последние доступные годы
            - Применена линейная экстраполяция трендов
            - Учтена индивидуальная динамика каждого ВУЗа
            - Прогноз построен на основе исторических данных
            """)
            
            # Скачивание результатов
            st.subheader("📥 Скачать результаты")
            csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💾 Скачать прогноз (CSV)",
                data=csv,
                file_name="прогноз_вузов_2024.csv",
                mime="text/csv"
            )
            
        else:
            progress_bar.empty()
            status_text.empty()
            st.warning("❌ Не удалось построить прогноз. Проверьте структуру данных.")
            
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Ошибка: {str(e)}")

else:
    st.info("""
    👆 **Загрузите файлы данных для анализа**
    
    **Ожидаемые данные:**
    - Файлы мониторинга за 2015, 2020, 2021, 2022 годы
    - Данные должны содержать названия ВУЗов и числовые показатели
    
    **Что будет проанализировано:**
    - Динамика ключевых показателей за последние годы
    - Прогноз значений на 2024 год
    - Рейтинг ВУЗов по прогнозируемым показателям
    - Визуализация трендов и распределений

    """)
        # Разработана студентами политехнического колледжа МУКР Исаевым Нурданом, Харкей Арафатом, Курманбековым Чынтемиром
