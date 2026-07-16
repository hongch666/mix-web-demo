package vectorreason

import "app/common/constants"

// Generate 生成向量语义原因
func Generate(vecScore float64) string {
	if vecScore >= 0.8 {
		return constants.VECTOR_REASON_HIGH
	}
	if vecScore >= 0.6 {
		return constants.VECTOR_REASON_MEDIUM
	}
	if vecScore > 0 {
		return constants.VECTOR_REASON_LOW
	}
	return ""
}
