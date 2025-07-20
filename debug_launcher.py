import importlib.util
import os
import sys
import logging

logging.basicConfig(filename='logs/debug_agent.log', level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')

if __name__ == '__main__':
    logging.info("🟡 Импорт main.py через importlib")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_pos_agent'))

    try:
        module_path = os.path.join(os.path.dirname(__file__), 'smart_pos_agent', 'main.py')
        spec = importlib.util.spec_from_file_location("smart_pos_main", module_path)
        agent_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_main)
        agent_main.run()
    except Exception as e:
        logging.error(f"Ошибка импорта main.py: {e}", exc_info=True)