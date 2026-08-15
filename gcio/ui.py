"""Shared Tailwind utility class strings applied to Django form widgets via `attrs={'class': ...}`."""

INPUT_CLASS = (
    'w-full px-3.5 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 '
    'focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900/40 transition-all'
)
SELECT_CLASS = INPUT_CLASS
TEXTAREA_CLASS = INPUT_CLASS
CHECKBOX_CLASS = 'w-[18px] h-[18px] accent-blue-600 shrink-0 cursor-pointer'
MULTISELECT_CLASS = INPUT_CLASS + ' min-h-[110px]'
