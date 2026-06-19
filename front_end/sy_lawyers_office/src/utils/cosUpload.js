/**
 * COS 直传工具 — 使用后端 STS 临时凭证上传文件到腾讯云对象存储
 *
 * 用法：
 *   import { uploadToCOS } from '@/utils/cosUpload'
 *   const result = await uploadToCOS(file, stsResponse, (pct) => console.log(pct))
 */

import COS from 'cos-js-sdk-v5'

/**
 * @param {File} file          浏览器 File 对象
 * @param {Object} stsResponse 后端返回的 STS 响应
 *   { credentials: { tmp_secret_id, tmp_secret_key, session_token },
 *     bucket, region, key }
 * @param {Function} [onProgress]  进度回调 (0-100)
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export function uploadToCOS(file, stsResponse, onProgress) {
  const { credentials, bucket, region, key } = stsResponse

  const cos = new COS({
    getAuthorization: (_options, callback) => {
      callback({
        TmpSecretId: credentials.tmp_secret_id,
        TmpSecretKey: credentials.tmp_secret_key,
        SecurityToken: credentials.session_token,
        StartTime: Math.floor(Date.now() / 1000) - 60,
        ExpiredTime: Math.floor(Date.now() / 1000) + 1800,
      })
    },
  })

  return new Promise((resolve) => {
    cos.putObject(
      {
        Bucket: bucket,
        Region: region,
        Key: key,
        Body: file,
        onProgress: (info) => {
          if (onProgress) onProgress(Math.round(info.percent * 100))
        },
      },
      (err) => {
        if (err) {
          console.error('[COS Upload] 上传失败:', err)
          resolve({ success: false, error: err.message || 'COS 上传失败' })
        } else {
          resolve({ success: true, file_size: file.size })
        }
      }
    )
  })
}
