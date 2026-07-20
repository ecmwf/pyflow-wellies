# Capture exit status immediately to detect context
# from environment, EXIT_REASON, EXIT_RC, and EXIT_DETAIL are set by pyflow's ERROR Function
local EMAIL_SUBJECT=""
local EMAIL_BODY=""
local EMAIL_IS_HTML=0
local TASK_PATH=%ECF_NAME%
local HOST=%ECF_HOST%
local NOTIFY=%MAIL_TYPE:%
local TO=%MAIL_USER:%
local EXIT_STATUS="${EXIT_RC:-0}"

# Decode exit status to determine context and build appropriate message
ELAPSED=$(( ${SLURM_JOB_END_TIME:-0} - ${SLURM_JOB_START_TIME:-0} ))
EMAIL_BODY="Running on $HOSTNAME as ${USER} after ${ELAPSED} seconds\\n"

if [[ ${EXIT_STATUS} -eq 0 ]]; then
    # Exit status == 0: successful completion
    EXIT_REASON="completed successfully"
    EMAIL_SUBJECT="[SUCCESS] Job ${TASK_PATH} completed in attempt "%ECF_TRYNO%
    EMAIL_BODY=$EMAIL_BODY"Job ${HOST}:${TASK_PATH} completed successfully"
else
    EXIT_REASON="failed with exit code ${EXIT_STATUS}"
    EMAIL_SUBJECT="[ABORT] Job ${TASK_PATH} failed in attempt "%ECF_TRYNO%
    EMAIL_BODY="<html><body style=\"margin:0; padding:0;\"><p style=\"margin:0 0 12px 0;\">Running on ${HOSTNAME} as ${USER} after ${ELAPSED} seconds</p><p style=\"margin:0 0 12px 0;\">Job ${HOST}:${TASK_PATH} was terminated with exit status: ${EXIT_STATUS}<br/>job file: %ECF_JOB%<br/>log file: %ECF_JOBOUT%</p>"
    traceback=$(grep -m 1 -A 5 -B 20 -n ERROR %ECF_JOBOUT%)
    traceback_escaped=$(printf '%%s' "${traceback}" | sed -e 's/&/\\&amp;/g' -e 's/</\\&lt;/g' -e 's/>/\\&gt;/g')
    EMAIL_BODY=$EMAIL_BODY"<table border=\"0\" cellpadding=\"10\" cellspacing=\"0\" width=\"600\" bgcolor=\"#f5f5f5\" style=\"background-color:#f5f5f5; border:1px solid #dddddd; border-collapse:collapse; width:600px;\"><tr><td bgcolor=\"#f5f5f5\" style=\"background-color:#f5f5f5;\"><pre style=\"margin:0; font-family:Consolas,'Courier New',monospace; font-size:12px; color:#333333; white-space:pre-wrap;\">${traceback_escaped}</pre></td></tr></table></body></html>"
    EMAIL_IS_HTML=1
fi

# Send email notification based on configuration and context
if [[ -n "${NOTIFY:-}" && -n "${TO:-}" ]]; then
    local should_mail=0
    # Determine if we should send email
    if [[ "${NOTIFY}" == "ALL" ]]; then
        # Send on all conditions
        should_mail=1
    elif [[ "${NOTIFY}" == "FAIL" ]] && [[ ${EXIT_STATUS} -ne 0 ]]; then
        # Send only on failure (non-zero exit)
        should_mail=1
    fi

    if [[ ${should_mail} -eq 1 ]]; then
        echo "Sending notification to ${TO}: ${EXIT_REASON}"
        if [[ ${EMAIL_IS_HTML} -eq 1 ]]; then
            local mail_tmp=$(mktemp) || true
            if [[ -n "${mail_tmp}" ]]; then
                {
                    printf "To: %%s\n" "${TO}"
                    printf "Subject: %%s\n" "${EMAIL_SUBJECT}"
                    printf "MIME-Version: 1.0\n"
                    printf "Content-Type: text/html; charset=UTF-8\n"
                    printf "\n"
                    printf "%%s" "${EMAIL_BODY}"
                } > "${mail_tmp}"
                sendmail -t < "${mail_tmp}" 2>/dev/null || true
                rm -f "${mail_tmp}"
            fi
        else
            echo -e "${EMAIL_BODY}" | mailx -s "${EMAIL_SUBJECT}" "${TO}" 2>/dev/null || true
        fi
    fi
fi
