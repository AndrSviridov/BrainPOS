from smart_pos_agent.gui import assistant_ui
import logging

logging.basicConfig(filename='logs/agent.log', level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')


def run():
    logging.debug("Launching GUI assistant...")
    assistant_ui.launch_ui()


if __name__ == '__main__':
    run()