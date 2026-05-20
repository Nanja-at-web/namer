function initSetupWizard () {
  const form = document.querySelector('#setup-wizard')
  if (!form) {
    return
  }

  const status = form.querySelector('#setupWizardStatus')
  const submitButton = form.querySelector('#saveSetupButton')
  const testNfsButton = form.querySelector('#testNfsAccess')
  const defaultSubmitText = submitButton?.textContent ?? 'Save setup'
  const defaultTestText = testNfsButton?.textContent ?? 'Test NFS access'
  const fieldNames = [
    'tpdbToken',
    'nasHost',
    'nasShare',
    'watchDir',
    'workDir',
    'failedDir',
    'destDir',
    'storageMode',
    'nasMountPath',
    'nasMountOptions'
  ]
  const snakeToCamelMap = {
    tpdb_token: 'tpdbToken',
    nas_host: 'nasHost',
    nas_share: 'nasShare',
    watch_dir: 'watchDir',
    work_dir: 'workDir',
    failed_dir: 'failedDir',
    dest_dir: 'destDir',
    storage_mode: 'storageMode',
    nas_mount_path: 'nasMountPath',
    nas_mount_options: 'nasMountOptions'
  }

  function setStatus (type, message) {
    status.className = `alert alert-${type}`
    status.textContent = message
    status.classList.remove('d-none')
  }

  function clearStatus () {
    status.className = 'alert d-none'
    status.textContent = ''
  }

  function clearErrors () {
    fieldNames.forEach(function (name) {
      const field = form.elements.namedItem(name)
      if (!(field instanceof HTMLElement)) {
        return
      }

      field.classList.remove('is-invalid')

      const feedback = field.parentElement?.querySelector('.invalid-feedback')
      if (feedback) {
        feedback.textContent = ''
      }
    })
  }

  function renderErrors (errors) {
    clearErrors()

    Object.entries(errors).forEach(function ([name, message]) {
      const lookup = snakeToCamelMap[name] ?? name
      const field = form.elements.namedItem(lookup)
      if (!(field instanceof HTMLElement)) {
        return
      }

      field.classList.add('is-invalid')
      const feedback = field.parentElement?.querySelector('.invalid-feedback')
      if (feedback) {
        feedback.textContent = String(message)
      }
    })
  }

  function setBusy (button, busy, busyText, idleText) {
    if (!button) {
      return
    }

    button.disabled = busy
    button.textContent = busy ? busyText : idleText
  }

  function serializeForm () {
    const formData = new FormData(form)
    return Object.fromEntries(formData.entries())
  }

  async function postJson (url, payload) {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    let body = {}
    try {
      body = await response.json()
    } catch {
      body = {}
    }

    return {
      ok: response.ok,
      status: response.status,
      body
    }
  }

  async function validateIfAvailable (payload) {
    const validateUrl = form.dataset.validateUrl
    if (!validateUrl) {
      return { ok: true, body: {} }
    }

    const result = await postJson(validateUrl, payload)

    if (result.status === 404 || result.status === 405) {
      return { ok: true, unavailable: true, body: {} }
    }

    return result
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault()
    clearStatus()
    clearErrors()

    const payload = serializeForm()
    setBusy(submitButton, true, 'Saving...', defaultSubmitText)

    try {
      const validation = await validateIfAvailable(payload)
      if (!validation.ok && validation.body?.errors) {
        renderErrors(validation.body.errors)
        setStatus('danger', 'Please fix the highlighted fields and try again.')
        return
      }

      const saveUrl = form.dataset.apiUrl
      if (!saveUrl) {
        setStatus('warning', 'Save is not configured for this page yet.')
        return
      }

      const result = await postJson(saveUrl, payload)
      if (result.status === 404 || result.status === 405) {
        setStatus('warning', 'The save endpoint is not available yet. Your values are still in the form for review.')
        return
      }

      if (!result.ok) {
        if (result.body?.errors) {
          renderErrors(result.body.errors)
        }
        setStatus('danger', result.body?.message ?? 'Setup could not be saved right now.')
        return
      }

      if (result.body?.errors && Object.keys(result.body.errors).length > 0) {
        renderErrors(result.body.errors)
        setStatus('danger', 'Please fix the highlighted fields and try again.')
        return
      }

      if (result.body?.redirect) {
        window.location.assign(result.body.redirect)
        return
      }

      if (validation.unavailable) {
        setStatus('success', 'Save request completed. Validation endpoint is not available yet, so server-side checks were skipped.')
        return
      }

      setStatus('success', 'Setup request completed.')
    } catch {
      setStatus('danger', 'Network error while contacting the setup service.')
    } finally {
      setBusy(submitButton, false, 'Saving...', defaultSubmitText)
    }
  })

  testNfsButton?.addEventListener('click', async function () {
    clearStatus()
    clearErrors()

    const testUrl = form.dataset.testNfsUrl
    if (!testUrl) {
      setStatus('warning', 'NFS test is not configured for this page yet.')
      return
    }

    setBusy(testNfsButton, true, 'Testing...', defaultTestText)

    try {
      const result = await postJson(testUrl, serializeForm())

      if (result.status === 404 || result.status === 405) {
        setStatus('warning', 'The NFS test endpoint is not available yet.')
        return
      }

      if (!result.ok) {
        if (result.body?.errors) {
          renderErrors(result.body.errors)
        }
        setStatus('danger', result.body?.message ?? 'NFS connectivity test failed.')
        return
      }

      if (result.body?.errors && Object.keys(result.body.errors).length > 0) {
        renderErrors(result.body.errors)
        setStatus('danger', 'Please fix the highlighted fields before testing NFS access.')
        return
      }

      setStatus('success', result.body?.message ?? 'NFS connectivity test completed.')
    } catch {
      setStatus('danger', 'Network error while testing NFS access.')
    } finally {
      setBusy(testNfsButton, false, 'Testing...', defaultTestText)
    }
  })
}

initSetupWizard()
