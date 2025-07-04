
import logging

def handle_poll_create(bot, msg_from_id, args_str, **kwargs):
    try:
        parts = [p.strip() for p in args_str.split('"') if p.strip()]
        if len(parts) < 3: raise ValueError('Usage: poll "Question" "Option A" "Option B" ...')

        question, options = parts[0], parts[1:]
        if len(options) > 10: raise ValueError("Error: Maximum 10 options allowed.")

        poll_id = bot.next_poll_id
        bot.next_poll_id += 1
        bot.polls[poll_id] = {'q': question, 'opts': options, 'votes': {}}

        poll_msg = [f"--- Poll #{poll_id} Created ---", f"Q: {question}"]
        poll_msg.extend(f" {i+1}. {opt}" for i, opt in enumerate(options))
        poll_msg.append(f"To vote, PM me: vote {poll_id} <option_number>")

        if bot._in_channel:
            bot._send_channel_message(bot._target_channel_id, "\n".join(poll_msg))
            bot._send_pm(msg_from_id, f"Poll #{poll_id} created in channel.")
        else:
            bot._send_pm(msg_from_id, "\n".join(poll_msg))
    except ValueError as e:
        bot._send_pm(msg_from_id, str(e))
    except Exception as e:
        logging.error(f"Error creating poll: {e}")
        bot._send_pm(msg_from_id, "Error creating poll. Use double quotes for question and options.")

def handle_vote(bot, msg_from_id, args_str, **kwargs):
    try:
        poll_id_str, vote_num_str = args_str.split(maxsplit=1)
        poll_id, vote_num = int(poll_id_str), int(vote_num_str)

        if poll_id not in bot.polls: raise ValueError(f"Error: Poll #{poll_id} not found.")
        
        poll_data = bot.polls[poll_id]
        if not (1 <= vote_num <= len(poll_data['opts'])): raise ValueError(f"Error: Invalid option. Choose 1-{len(poll_data['opts'])}.")
        
        poll_data['votes'][msg_from_id] = vote_num - 1
        bot._send_pm(msg_from_id, f"Vote for '{poll_data['opts'][vote_num - 1]}' in Poll #{poll_id} recorded.")
    except (ValueError, IndexError) as e:
        bot._send_pm(msg_from_id, str(e) or "Usage: vote <poll_id> <option_number>")

def handle_results(bot, msg_from_id, args_str, **kwargs):
    try:
        poll_id_str = args_str.strip()
        if not poll_id_str:
            active_polls = ', '.join(map(str, bot.polls.keys())) or "None"
            bot._send_pm(msg_from_id, f"Active Polls: {active_polls}. Usage: results <poll_id>"); return

        poll_id = int(poll_id_str)
        if poll_id not in bot.polls: raise ValueError(f"Error: Poll #{poll_id} not found.")

        poll_data = bot.polls[poll_id]
        total_votes = len(poll_data['votes'])
        results = [0] * len(poll_data['opts'])
        for vote_idx in poll_data['votes'].values(): results[vote_idx] += 1

        result_msg = [f"--- Poll #{poll_id} Results ---", f"Q: {poll_data['q']}", f"Total Votes: {total_votes}"]
        for i, opt_text in enumerate(poll_data['opts']):
            count = results[i]
            percent = (count / total_votes * 100) if total_votes > 0 else 0
            result_msg.append(f" {i+1}. {opt_text} - {count} votes ({percent:.1f}%)")
        
        bot._send_pm(msg_from_id, "\n".join(result_msg))
    except ValueError as e:
        bot._send_pm(msg_from_id, str(e) or "Usage: results <poll_id>")
